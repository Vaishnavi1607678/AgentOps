# AgentOps

**An autonomous DevOps agent, fully observed.**

AgentOps investigates infrastructure incidents using real tool calls checking service health, reading logs, restarting, deploying, rolling back and streams every step of its reasoning to a live dashboard. Nothing destructive happens without a human clicking approve first.

🔗 **Demo video:** https://drive.google.com/file/d/1rjEUFRgvd9nh8N9Zww5uwYenR-H72d4_/view?usp=sharing

---

## What it does

Give the agent a task in plain English:

> "Investigate why checkout-service is slow and fix it."

It checks service status and logs, reasons about what's wrong, and proposes an action all visible in real time on the dashboard. If the fix requires something destructive (a restart, a deploy, a rollback), the agent **stops and waits**. A human has to click Approve before anything actually happens.

Every step is logged: what the agent was thinking, which tool it called, what came back, how long it took, how many tokens it used.

## Why it's built this way

Most "AI agent" demos either can't take real actions, or take them with no safety net. AgentOps does both things properly:

- **It's a real agent** it calls actual tools against a live service registry, not a chat window pretending to be one.
- **It's safe by construction, not by prompt.** The approval gate is a state machine: the backend literally will not execute a destructive tool call until a human has flipped a flag in the database. You can't prompt-inject your way around it.
- **It's observable.** Every reasoning step and tool call is traced and streamed live the same pattern production LLM ops teams use to debug and trust agent behavior.

## Screenshots

<img width="1892" height="942" alt="image" src="https://github.com/user-attachments/assets/111823b6-5dd1-48d0-991a-5092ab638c53" />

<img width="1917" height="963" alt="image" src="https://github.com/user-attachments/assets/1e5a7ffe-18a2-4193-8633-38245a0265de" />

<img width="1916" height="857" alt="image" src="https://github.com/user-attachments/assets/94bfa57f-0beb-4c9d-bb32-bd19d80da8b5" />


## Architecture


<img width="595" height="553" alt="image" src="https://github.com/user-attachments/assets/9911fa9f-d550-4aec-867f-fdfd578f11ff" />



The mock infrastructure layer simulates a small fleet of services so the whole project runs with zero external dependencies beyond an OpenAI API key. Swap it for real Prometheus/Loki/Kubernetes calls and the agent loop and dashboard don't change — that's the point of the abstraction.

## Tech stack

| Layer | Tech |
|---|---|
| Agent orchestration | Python, FastAPI, OpenAI function calling |
| Trace storage | SQLite (SQLModel) |
| Live updates | Server-Sent Events (SSE) |
| Dashboard | Next.js 14, TypeScript, Tailwind CSS |
| Deployment | Render (backend) · Vercel (frontend) |

## Key features

-  **Multi-step reasoning traced live** — every thought, tool call, and result streams to the dashboard as it happens, not after the fact
-  **Human-in-the-loop safety gate** — destructive actions (restart, deploy, rollback) pause execution and require explicit approval
-  **Full observability** — latency, token usage, and tool inputs/outputs logged per step
-  **Real tool-calling agent loop** — built on OpenAI's function calling, not a scripted demo

## Quick start

**1. Clone and enter the project**
```bash
git clone https://github.com/Vaishnavi1607678/AgentOps.git
cd AgentOps/agentops
```

**2. Start the backend**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # add your OPENAI_API_KEY
uvicorn main:app --reload --port 8000
```

**3. Start the dashboard** (new terminal)
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

**4. Open [localhost:3000](http://localhost:3000)**, give the agent a task, and watch it work.

## Roadmap

- [ ] Swap mock tools for real Prometheus / Loki / Kubernetes API calls
- [ ] Eval harness: replay past incidents, score diagnosis accuracy
- [ ] Cost tracking (tokens × model price) in the dashboard
- [ ] Postgres backend for multi-instance deployments
- [ ] Expose the tool layer as an MCP server

## License

MIT
