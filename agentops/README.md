# AgentOps

An autonomous DevOps agent, fully observed. AgentOps investigates infrastructure problems
using real tool calls (service status, logs, restarts, deploys, rollbacks), and every step
— reasoning, tool call, tool result, latency, tokens — is traced live in a dashboard.
Destructive actions (restart, deploy, rollback) pause the agent and wait for a human to
approve or deny them before executing.

Two things in one project: an **agent that acts**, and an **observability platform that
watches it act**.

## Architecture

```
Next.js dashboard (Vercel)  <--REST + SSE-->  FastAPI agent service (Render/Railway)
        |                                              |
   run list, live trace,                    Claude tool-use loop, SQLite
   approve/deny UI                          trace store, approval gate
                                                        |
                                              mock infrastructure
                                              (services, logs, deploys)
```

The mock infrastructure (`backend/tools.py`) simulates a small fleet of services so the
whole thing runs with zero external dependencies beyond an Anthropic API key. In a real
deployment, swap those functions for calls to Prometheus, Loki, and the Kubernetes API —
the agent loop and dashboard don't change.

## Repo layout

```
backend/     FastAPI service — agent loop, tools, trace storage, SSE stream
frontend/    Next.js dashboard — run list, live trace timeline, approval UI
```

## Run it locally

**Backend**
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your OPENAI_API_KEY
uvicorn main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
cp .env.local.example .env.local   # points at http://localhost:8000 by default
npm run dev
```

Open `http://localhost:3000`, type a task like *"Investigate why checkout-service is slow
and fix it"*, and watch the agent work. When it proposes a restart/deploy/rollback, approve
or deny it right in the dashboard.

## Deploy it live

**Backend → Render**
1. Push this repo to GitHub.
2. On [render.com](https://render.com): New → Web Service → connect the repo, root
   directory `backend`.
3. Render auto-detects the `Dockerfile`. Set environment variables: `OPENAI_API_KEY`,
   `ALLOWED_ORIGINS` (your Vercel URL once you have it, comma-separated if more than one).
4. Deploy. Note the resulting URL, e.g. `https://agentops-api.onrender.com`.

**Frontend → Vercel**
1. On [vercel.com](https://vercel.com): New Project → import the repo, root directory
   `frontend`.
2. Add environment variable `NEXT_PUBLIC_API_URL` = your Render backend URL.
3. Deploy. You now have a live link for your resume/portfolio.
4. Go back to Render and update `ALLOWED_ORIGINS` to include the Vercel URL, redeploy.

Render's free tier spins down when idle, so the first request after inactivity can take
~30s to wake up — worth a line in your project description or demo video so it doesn't
look broken.

## What to say about it on a resume

- "Built an autonomous DevOps agent (OpenAI function calling, FastAPI) that investigates and
  remediates service incidents, with human-in-the-loop approval gating all destructive
  actions."
- "Built a full-trace LLM observability dashboard (Next.js, SSE) surfacing every
  reasoning step, tool call, latency, and token count in real time."
- Quantify once you've run it: e.g. "reduced mean time to diagnosis from N steps to M by
  giving the agent structured log/status tools instead of raw text."

## Extending it (good "future work" talking points in an interview)

- Swap the mock tools for real Prometheus/Loki/k8s API calls.
- Add a proper eval harness: replay past incidents, score whether the agent reached the
  right diagnosis and proposed the right fix.
- Persist traces to Postgres instead of SQLite for multi-instance deployments.
- Add cost tracking (tokens × model price) to the dashboard.
- Turn the tool layer into an MCP server so any MCP-compatible agent (not just this one)
  can operate the same infrastructure.
