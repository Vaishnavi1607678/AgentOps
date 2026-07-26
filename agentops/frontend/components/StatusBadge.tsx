import { RunStatus } from "@/lib/api";

const STYLES: Record<RunStatus, { dot: string; text: string; label: string }> = {
  running: { dot: "bg-signal pulse", text: "text-signal", label: "running" },
  paused_for_approval: { dot: "bg-amber pulse", text: "text-amber", label: "needs approval" },
  completed: { dot: "bg-success", text: "text-success", label: "completed" },
  failed: { dot: "bg-danger", text: "text-danger", label: "failed" },
};

export default function StatusBadge({ status }: { status: RunStatus }) {
  const s = STYLES[status];
  return (
    <span className={`inline-flex items-center gap-1.5 text-[11px] font-mono uppercase tracking-wide ${s.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
      {s.label}
    </span>
  );
}
