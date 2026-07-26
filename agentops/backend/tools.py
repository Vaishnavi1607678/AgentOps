"""
Mock infrastructure the agent operates on. In a real deployment these functions
would call your actual observability stack (Prometheus, Loki, k8s API, etc).
Kept in-memory here so the whole project runs with zero external dependencies.
"""
import random
import time
from datetime import datetime, timedelta

# --- fake fleet state -------------------------------------------------------

_SERVICES = {
    "checkout-service": {"status": "degraded", "cpu": 91, "mem": 74, "p99_ms": 1840, "error_rate": 0.12, "version": "v2.3.1"},
    "auth-service": {"status": "healthy", "cpu": 34, "mem": 41, "p99_ms": 120, "error_rate": 0.001, "version": "v1.9.0"},
    "inventory-service": {"status": "healthy", "cpu": 22, "mem": 38, "p99_ms": 90, "error_rate": 0.0, "version": "v3.1.4"},
    "notification-service": {"status": "healthy", "cpu": 18, "mem": 25, "p99_ms": 60, "error_rate": 0.0, "version": "v1.2.2"},
}

_LOG_SAMPLES = {
    "checkout-service": [
        "WARN  connection pool exhausted, waiting for available connection (pool_size=20)",
        "ERROR upstream timeout calling payment-gateway after 5000ms",
        "ERROR upstream timeout calling payment-gateway after 5000ms",
        "WARN  GC pause 840ms (G1 Young Generation)",
        "ERROR failed to acquire DB connection: timeout after 3000ms",
        "INFO  request completed status=504 duration_ms=5012",
    ],
    "auth-service": [
        "INFO  request completed status=200 duration_ms=45",
        "INFO  token refresh succeeded for client_id=web-app",
    ],
}

_DEPLOY_HISTORY = {
    "checkout-service": ["v2.1.0", "v2.2.0", "v2.3.0", "v2.3.1"],
}


def _latency():
    time.sleep(random.uniform(0.15, 0.5))


# --- tool implementations ---------------------------------------------------

def get_service_status(service_name: str):
    _latency()
    svc = _SERVICES.get(service_name)
    if not svc:
        return {"error": f"no such service '{service_name}'", "known_services": list(_SERVICES.keys())}
    return {"service": service_name, **svc, "checked_at": datetime.utcnow().isoformat()}


def list_services():
    _latency()
    return {"services": [{"name": k, "status": v["status"]} for k, v in _SERVICES.items()]}


def get_logs(service_name: str, lines: int = 20):
    _latency()
    samples = _LOG_SAMPLES.get(service_name, ["INFO  request completed status=200 duration_ms=52"])
    now = datetime.utcnow()
    entries = []
    for i in range(min(lines, 30)):
        line = samples[i % len(samples)]
        ts = (now - timedelta(seconds=(lines - i) * 4)).strftime("%H:%M:%S")
        entries.append(f"[{ts}] {line}")
    return {"service": service_name, "log_lines": entries}


def restart_service(service_name: str, reason: str):
    """DESTRUCTIVE — requires human approval before execution."""
    _latency()
    if service_name not in _SERVICES:
        return {"error": f"no such service '{service_name}'"}
    _SERVICES[service_name]["status"] = "healthy"
    _SERVICES[service_name]["cpu"] = random.randint(15, 30)
    _SERVICES[service_name]["error_rate"] = 0.0
    _SERVICES[service_name]["p99_ms"] = random.randint(60, 130)
    return {"service": service_name, "action": "restarted", "reason": reason, "new_status": "healthy"}


def deploy_version(service_name: str, version: str):
    """DESTRUCTIVE — requires human approval before execution."""
    _latency()
    if service_name not in _SERVICES:
        return {"error": f"no such service '{service_name}'"}
    _SERVICES[service_name]["version"] = version
    _DEPLOY_HISTORY.setdefault(service_name, []).append(version)
    return {"service": service_name, "action": "deployed", "version": version}


def rollback_version(service_name: str):
    """DESTRUCTIVE — requires human approval before execution."""
    _latency()
    hist = _DEPLOY_HISTORY.get(service_name, [])
    if len(hist) < 2:
        return {"error": "no previous version to roll back to"}
    hist.pop()
    prev = hist[-1]
    _SERVICES[service_name]["version"] = prev
    return {"service": service_name, "action": "rolled_back", "version": prev}


TOOL_IMPLS = {
    "get_service_status": get_service_status,
    "list_services": list_services,
    "get_logs": get_logs,
    "restart_service": restart_service,
    "deploy_version": deploy_version,
    "rollback_version": rollback_version,
}

DESTRUCTIVE_TOOLS = {"restart_service", "deploy_version", "rollback_version"}

# --- Anthropic tool schemas --------------------------------------------------

TOOL_SCHEMAS = [
    {
        "name": "list_services",
        "description": "List all services in the fleet with their current status.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_service_status",
        "description": "Get detailed health metrics (CPU, memory, p99 latency, error rate, version) for a service.",
        "input_schema": {
            "type": "object",
            "properties": {"service_name": {"type": "string"}},
            "required": ["service_name"],
        },
    },
    {
        "name": "get_logs",
        "description": "Fetch recent log lines for a service.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string"},
                "lines": {"type": "integer", "description": "number of log lines to fetch, default 20"},
            },
            "required": ["service_name"],
        },
    },
    {
        "name": "restart_service",
        "description": "Restart a service. DESTRUCTIVE action — requires human approval.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string"},
                "reason": {"type": "string", "description": "why the restart is needed"},
            },
            "required": ["service_name", "reason"],
        },
    },
    {
        "name": "deploy_version",
        "description": "Deploy a specific version to a service. DESTRUCTIVE action — requires human approval.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string"},
                "version": {"type": "string"},
            },
            "required": ["service_name", "version"],
        },
    },
    {
        "name": "rollback_version",
        "description": "Roll a service back to its previous deployed version. DESTRUCTIVE action — requires human approval.",
        "input_schema": {
            "type": "object",
            "properties": {"service_name": {"type": "string"}},
            "required": ["service_name"],
        },
    },
]

# OpenAI's Chat Completions "tools" format wraps the same schema differently:
# {"type": "function", "function": {"name", "description", "parameters"}}
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t["description"],
            "parameters": t["input_schema"],
        },
    }
    for t in TOOL_SCHEMAS
]
