"use client";
import { RunSummary } from "@/lib/api";
import StatusBadge from "./StatusBadge";

export default function RunList({
  runs,
  selectedId,
  onSelect,
}: {
  runs: RunSummary[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}) {
  if (runs.length === 0) {
    return (
      <div className="px-4 py-8 text-center text-muted text-sm">
        No runs yet. Give the agent a task to start its first trace.
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      {runs.map((run) => (
        <button
          key={run.id}
          onClick={() => onSelect(run.id)}
          className={`text-left px-4 py-3 border-b border-line transition-colors ${
            selectedId === run.id ? "bg-raised" : "hover:bg-raised/50"
          }`}
        >
          <div className="flex items-center justify-between mb-1.5">
            <span className="font-mono text-[11px] text-muted">#{run.id}</span>
            <StatusBadge status={run.status} />
          </div>
          <p className="text-sm text-ink line-clamp-2 leading-snug">{run.task}</p>
          <p className="text-[11px] text-muted mt-1.5 font-mono">
            {run.total_tokens_in + run.total_tokens_out} tok
          </p>
        </button>
      ))}
    </div>
  );
}
