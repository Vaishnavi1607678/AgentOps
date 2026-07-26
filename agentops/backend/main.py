import asyncio
import json
import os

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select
from sse_starlette.sse import EventSourceResponse

from db import engine, init_db
from models import Run, Step
import agent

app = FastAPI(title="AgentOps API")

origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


class NewRunRequest(BaseModel):
    task: str


class ApprovalRequest(BaseModel):
    approved: bool


def _run_dict(run: Run) -> dict:
    return {
        "id": run.id,
        "task": run.task,
        "status": run.status,
        "model": run.model,
        "total_tokens_in": run.total_tokens_in,
        "total_tokens_out": run.total_tokens_out,
        "created_at": run.created_at.isoformat(),
        "updated_at": run.updated_at.isoformat(),
    }


@app.post("/runs")
async def create_run(req: NewRunRequest):
    run_id = await agent.start_run(req.task)
    return {"run_id": run_id}


@app.get("/runs")
def list_runs():
    with Session(engine) as session:
        runs = session.exec(select(Run).order_by(Run.created_at.desc())).all()
        return [_run_dict(r) for r in runs]


@app.get("/runs/{run_id}")
def get_run(run_id: int):
    with Session(engine) as session:
        run = session.get(Run, run_id)
        if not run:
            raise HTTPException(404, "run not found")
        steps = session.exec(select(Step).where(Step.run_id == run_id).order_by(Step.seq)).all()
        return {"run": _run_dict(run), "steps": [agent._step_dict(s) for s in steps]}


@app.post("/steps/{step_id}/approve")
async def approve(step_id: int, req: ApprovalRequest):
    result = await agent.approve_step(step_id, req.approved)
    return result


@app.get("/runs/{run_id}/stream")
async def stream(run_id: int):
    queue = agent.subscribe(run_id)

    async def event_gen():
        try:
            while True:
                event = await queue.get()
                yield {"event": event["event"], "data": json.dumps(event["data"])}
        except asyncio.CancelledError:
            agent.unsubscribe(run_id, queue)
            raise

    return EventSourceResponse(event_gen())


@app.get("/health")
def health():
    return {"status": "ok"}
