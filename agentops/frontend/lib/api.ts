export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type RunStatus = "running" | "paused_for_approval" | "completed" | "failed";

export interface RunSummary {
  id: number;
  task: string;
  status: RunStatus;
  model: string;
  total_tokens_in: number;
  total_tokens_out: number;
  created_at: string;
  updated_at: string;
}

export type StepType =
  | "reasoning"
  | "tool_call"
  | "tool_result"
  | "approval_pending"
  | "approval_granted"
  | "approval_denied"
  | "final"
  | "error";

export interface StepRecord {
  id: number;
  run_id: number;
  seq: number;
  type: StepType;
  content: string;
  tool_name: string | null;
  tool_input: string | null;
  tool_output: string | null;
  tool_use_id: string | null;
  requires_approval: boolean;
  latency_ms: number | null;
  created_at: string;
}

export async function listRuns(): Promise<RunSummary[]> {
  const res = await fetch(`${API_URL}/runs`, { cache: "no-store" });
  if (!res.ok) throw new Error("failed to list runs");
  return res.json();
}

export async function getRun(runId: number): Promise<{ run: RunSummary; steps: StepRecord[] }> {
  const res = await fetch(`${API_URL}/runs/${runId}`, { cache: "no-store" });
  if (!res.ok) throw new Error("failed to fetch run");
  return res.json();
}

export async function createRun(task: string): Promise<{ run_id: number }> {
  const res = await fetch(`${API_URL}/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task }),
  });
  if (!res.ok) throw new Error("failed to create run");
  return res.json();
}

export async function approveStep(stepId: number, approved: boolean): Promise<void> {
  const res = await fetch(`${API_URL}/steps/${stepId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approved }),
  });
  if (!res.ok) throw new Error("failed to submit approval");
}

export function streamRun(runId: number, onEvent: (event: string, data: any) => void): () => void {
  const source = new EventSource(`${API_URL}/runs/${runId}/stream`);
  source.onmessage = (e) => {
    try {
      const parsed = JSON.parse(e.data);
      onEvent("message", parsed);
    } catch {
      // ignore malformed frames
    }
  };
  source.addEventListener("step", (e: MessageEvent) => onEvent("step", JSON.parse(e.data)));
  source.addEventListener("run_status", (e: MessageEvent) => onEvent("run_status", JSON.parse(e.data)));
  return () => source.close();
}
