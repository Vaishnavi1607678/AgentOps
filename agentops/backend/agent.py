import asyncio
import json
import os
import time
from datetime import datetime
from typing import Dict, List

from openai import OpenAI
from sqlmodel import Session, select

from db import engine
from models import Run, Step
from tools import TOOL_IMPLS, OPENAI_TOOLS, DESTRUCTIVE_TOOLS

MODEL = os.getenv("AGENT_MODEL", "gpt-4o")
MAX_TURNS = 12

SYSTEM_PROMPT = """You are AgentOps, an autonomous DevOps assistant with real tools to inspect and operate
a fleet of services. Investigate methodically: check service status and logs before acting.
Propose exactly one action per turn — never call more than one tool in a single turn.
When you believe the task is resolved, reply with a short plain-text summary of what you found
and what you did, and do not call any more tools."""

# --- simple in-memory pub/sub for SSE streaming -----------------------------

_subscribers: Dict[int, List[asyncio.Queue]] = {}


def subscribe(run_id: int) -> asyncio.Queue:
    q = asyncio.Queue()
    _subscribers.setdefault(run_id, []).append(q)
    return q


def unsubscribe(run_id: int, q: asyncio.Queue):
    if run_id in _subscribers and q in _subscribers[run_id]:
        _subscribers[run_id].remove(q)


def publish(run_id: int, event: dict):
    for q in _subscribers.get(run_id, []):
        q.put_nowait(event)


client = OpenAI()  # reads OPENAI_API_KEY from env


def _log_step(session: Session, run_id: int, seq: int, **kwargs) -> Step:
    step = Step(run_id=run_id, seq=seq, **kwargs)
    session.add(step)
    session.commit()
    session.refresh(step)
    publish(run_id, {"event": "step", "data": _step_dict(step)})
    return step


def _step_dict(step: Step) -> dict:
    return {
        "id": step.id,
        "run_id": step.run_id,
        "seq": step.seq,
        "type": step.type,
        "content": step.content,
        "tool_name": step.tool_name,
        "tool_input": step.tool_input,
        "tool_output": step.tool_output,
        "tool_use_id": step.tool_use_id,
        "requires_approval": step.requires_approval,
        "latency_ms": step.latency_ms,
        "created_at": step.created_at.isoformat(),
    }


def _next_seq(session: Session, run_id: int) -> int:
    existing = session.exec(select(Step).where(Step.run_id == run_id)).all()
    return len(existing) + 1


def _assistant_message_dict(message) -> dict:
    """Convert an OpenAI ChatCompletionMessage into the plain dict we persist and replay."""
    d = {"role": "assistant", "content": message.content}
    if message.tool_calls:
        d["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in message.tool_calls
        ]
    return d


async def start_run(task: str) -> int:
    with Session(engine) as session:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task},
        ]
        run = Run(task=task, model=MODEL, messages_json=json.dumps(messages))
        session.add(run)
        session.commit()
        session.refresh(run)
        run_id = run.id
    asyncio.create_task(_execute_turn(run_id))
    return run_id


async def approve_step(step_id: int, approved: bool):
    with Session(engine) as session:
        step = session.get(Step, step_id)
        if not step or not step.requires_approval:
            return {"error": "not an approvable step"}
        step.type = "approval_granted" if approved else "approval_denied"
        session.add(step)
        session.commit()
        publish(step.run_id, {"event": "step", "data": _step_dict(step)})
        run_id = step.run_id

    # check whether all destructive steps for the current pending turn are resolved
    with Session(engine) as session:
        run = session.get(Run, run_id)
        pending = session.exec(
            select(Step).where(Step.run_id == run_id, Step.type == "approval_pending")
        ).all()
        if pending:
            return {"status": "waiting_on_other_approvals"}
        run.status = "running"
        session.add(run)
        session.commit()

    asyncio.create_task(_resume_after_approval(run_id))
    return {"status": "resumed"}


async def _resume_after_approval(run_id: int):
    with Session(engine) as session:
        run = session.get(Run, run_id)
        messages = json.loads(run.messages_json)
        last_assistant = messages[-1]
        tool_calls = last_assistant.get("tool_calls") or []

        decided_steps = session.exec(
            select(Step).where(
                Step.run_id == run_id,
                Step.type.in_(["approval_granted", "approval_denied"]),
            )
        ).all()
        decisions = {s.tool_use_id: s.type for s in decided_steps}

        seq = _next_seq(session, run_id)
        tool_messages = []
        for tc in tool_calls:
            name = tc["function"]["name"]
            tool_input = json.loads(tc["function"]["arguments"] or "{}")
            tool_id = tc["id"]

            if name in DESTRUCTIVE_TOOLS:
                decision = decisions.get(tool_id)
                if decision == "approval_denied":
                    result = {"denied": True, "note": "Human operator denied this action."}
                else:
                    t0 = time.time()
                    result = TOOL_IMPLS[name](**tool_input)
                    latency = int((time.time() - t0) * 1000)
                    _log_step(session, run_id, seq, type="tool_result", tool_name=name,
                              tool_output=json.dumps(result), tool_use_id=tool_id, latency_ms=latency)
                    seq += 1
            else:
                t0 = time.time()
                result = TOOL_IMPLS[name](**tool_input)
                latency = int((time.time() - t0) * 1000)
                _log_step(session, run_id, seq, type="tool_result", tool_name=name,
                          tool_output=json.dumps(result), tool_use_id=tool_id, latency_ms=latency)
                seq += 1

            tool_messages.append({"role": "tool", "tool_call_id": tool_id, "content": json.dumps(result)})

        messages.extend(tool_messages)
        run.messages_json = json.dumps(messages)
        run.status = "running"
        session.add(run)
        session.commit()

    await _execute_turn(run_id)


async def _execute_turn(run_id: int, turn: int = 0):
    if turn >= MAX_TURNS:
        with Session(engine) as session:
            run = session.get(Run, run_id)
            run.status = "failed"
            session.add(run)
            session.commit()
            seq = _next_seq(session, run_id)
            _log_step(session, run_id, seq, type="error", content="Max turns reached without resolution.")
            publish(run_id, {"event": "run_status", "data": {"status": "failed"}})
        return

    with Session(engine) as session:
        run = session.get(Run, run_id)
        messages = json.loads(run.messages_json)

    t0 = time.time()
    response = await asyncio.to_thread(
        client.chat.completions.create,
        model=MODEL,
        messages=messages,
        tools=OPENAI_TOOLS,
        tool_choice="auto",
    )
    latency = int((time.time() - t0) * 1000)

    message = response.choices[0].message
    assistant_dict = _assistant_message_dict(message)
    usage = response.usage

    with Session(engine) as session:
        run = session.get(Run, run_id)
        messages = json.loads(run.messages_json)
        messages.append(assistant_dict)
        run.messages_json = json.dumps(messages)
        run.total_tokens_in += usage.prompt_tokens if usage else 0
        run.total_tokens_out += usage.completion_tokens if usage else 0
        run.updated_at = datetime.utcnow()

        seq = _next_seq(session, run_id)
        if assistant_dict.get("content"):
            _log_step(session, run_id, seq, type="reasoning", content=assistant_dict["content"],
                      latency_ms=latency,
                      tokens_in=usage.prompt_tokens if usage else None,
                      tokens_out=usage.completion_tokens if usage else None)
            seq += 1

        tool_calls = assistant_dict.get("tool_calls") or []

        if not tool_calls:
            run.status = "completed"
            session.add(run)
            session.commit()
            final_text = assistant_dict.get("content") or "Task complete."
            _log_step(session, run_id, seq, type="final", content=final_text)
            publish(run_id, {"event": "run_status", "data": {"status": "completed"}})
            return

        destructive = [tc for tc in tool_calls if tc["function"]["name"] in DESTRUCTIVE_TOOLS]

        if destructive:
            run.status = "paused_for_approval"
            session.add(run)
            session.commit()
            for tc in destructive:
                _log_step(session, run_id, seq, type="approval_pending", tool_name=tc["function"]["name"],
                          tool_input=tc["function"]["arguments"], tool_use_id=tc["id"], requires_approval=True)
                seq += 1
            publish(run_id, {"event": "run_status", "data": {"status": "paused_for_approval"}})
            return

        session.add(run)
        session.commit()

        # no destructive calls this turn — execute immediately and continue the loop
        tool_messages = []
        for tc in tool_calls:
            name = tc["function"]["name"]
            tool_input = json.loads(tc["function"]["arguments"] or "{}")
            _log_step(session, run_id, seq, type="tool_call", tool_name=name,
                      tool_input=tc["function"]["arguments"], tool_use_id=tc["id"])
            seq += 1
            t1 = time.time()
            result = TOOL_IMPLS[name](**tool_input)
            tool_latency = int((time.time() - t1) * 1000)
            _log_step(session, run_id, seq, type="tool_result", tool_name=name,
                      tool_output=json.dumps(result), tool_use_id=tc["id"], latency_ms=tool_latency)
            seq += 1
            tool_messages.append({"role": "tool", "tool_call_id": tc["id"], "content": json.dumps(result)})

        messages = json.loads(run.messages_json)
        messages.extend(tool_messages)
        run.messages_json = json.dumps(messages)
        session.add(run)
        session.commit()

    await _execute_turn(run_id, turn + 1)
