"use client";
import { StepRecord } from "@/lib/api";

function prettyJson(raw: string | null): string {
  if (!raw) return "";
  try {
    return JSON.stringify(JSON.parse(raw), null, 2);
  } catch {
    return raw;
  }
}

export default function StepCard({
  step,
  onApprove,
}: {
  step: StepRecord;
  onApprove?: (stepId: number, approved: boolean) => void;
}) {
  const time = new Date(step.created_at).toLocaleTimeString([], { hour12: false });

  if (step.type === "reasoning") {
    return (
      <div className="rise pl-4 border-l-2 border-line">
        <div className="flex items-center gap-2 text-[11px] font-mono text-muted mb-1">
          <span>{time}</span>
          <span className="uppercase tracking-wide">reasoning</span>
        </div>
        <p className="text-sm text-ink/90 leading-relaxed">{step.content}</p>
      </div>
    );
  }

  if (step.type === "tool_call" || step.type === "approval_pending") {
    const pending = step.type === "approval_pending";
    return (
      <div className={`rise pl-4 border-l-2 rounded-r-md ${pending ? "border-amber bg-amber/5" : "border-signal/50"} py-2`}>
        <div className="flex items-center gap-2 text-[11px] font-mono text-muted mb-1.5">
          <span>{time}</span>
          <span className={`uppercase tracking-wide ${pending ? "text-amber" : "text-signal"}`}>
            {pending ? "awaiting approval" : "tool call"}
          </span>
        </div>
        <div className="font-mono text-sm bg-surface border border-line rounded-md px-3 py-2">
          <span className="text-signal">$</span> <span className="text-ink font-medium">{step.tool_name}</span>
          <span className="text-muted">({Object.entries(JSON.parse(step.tool_input || "{}"))
            .map(([k, v]) => `${k}="${v}"`)
            .join(", ")})</span>
        </div>
        {pending && onApprove && (
          <div className="flex items-center gap-2 mt-2.5">
            <button
              onClick={() => onApprove(step.id, true)}
              className="px-3 py-1.5 text-xs font-medium rounded-md bg-success/15 text-success border border-success/30 hover:bg-success/25 transition-colors"
            >
              Approve
            </button>
            <button
              onClick={() => onApprove(step.id, false)}
              className="px-3 py-1.5 text-xs font-medium rounded-md bg-danger/15 text-danger border border-danger/30 hover:bg-danger/25 transition-colors"
            >
              Deny
            </button>
            <span className="text-[11px] text-muted ml-1">destructive action — human sign-off required</span>
          </div>
        )}
      </div>
    );
  }

  if (step.type === "tool_result") {
    return (
      <div className="rise pl-4 border-l-2 border-line/60 -mt-2">
        <div className="text-[11px] font-mono text-muted mb-1">
          → result {step.latency_ms != null && <span className="text-muted/70">({step.latency_ms}ms)</span>}
        </div>
        <pre className="font-mono text-[12px] text-ink/70 bg-surface/60 border border-line rounded-md px-3 py-2 overflow-x-auto">
          {prettyJson(step.tool_output)}
        </pre>
      </div>
    );
  }

  if (step.type === "approval_granted" || step.type === "approval_denied") {
    const granted = step.type === "approval_granted";
    return (
      <div className="pl-4 text-[12px] font-mono">
        <span className={granted ? "text-success" : "text-danger"}>
          {granted ? "✓ approved" : "✕ denied"}
        </span>{" "}
        <span className="text-muted">by operator</span>
      </div>
    );
  }

  if (step.type === "final") {
    return (
      <div className="rise pl-4 border-l-2 border-success rounded-r-md bg-success/5 py-2.5">
        <div className="text-[11px] font-mono text-success uppercase tracking-wide mb-1">resolved</div>
        <p className="text-sm text-ink leading-relaxed">{step.content}</p>
      </div>
    );
  }

  if (step.type === "error") {
    return (
      <div className="rise pl-4 border-l-2 border-danger rounded-r-md bg-danger/5 py-2.5">
        <div className="text-[11px] font-mono text-danger uppercase tracking-wide mb-1">error</div>
        <p className="text-sm text-ink leading-relaxed">{step.content}</p>
      </div>
    );
  }

  return null;
}
