import { RunSummary } from "@/lib/api";
import StatusBadge from "./StatusBadge";

export default function MetricsBar({ run }: { run: RunSummary }) {
  return (
    <div className="border-b border-line px-5 py-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[11px] font-mono text-muted mb-1">RUN #{run.id}</p>
          <h2 className="text-base text-ink font-medium leading-snug">{run.task}</h2>
        </div>
        <StatusBadge status={run.status} />
      </div>
      <div className="flex gap-4 mt-3 text-[11px] font-mono text-muted">
        <span>model: {run.model}</span>
        <span>tokens in: {run.total_tokens_in}</span>
        <span>tokens out: {run.total_tokens_out}</span>
      </div>
    </div>
  );
}
