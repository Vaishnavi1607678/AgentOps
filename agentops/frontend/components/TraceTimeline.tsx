"use client";
import { RunStatus, StepRecord } from "@/lib/api";
import StepCard from "./StepCard";

export default function TraceTimeline({
  steps,
  status,
  onApprove,
}: {
  steps: StepRecord[];
  status: RunStatus;
  onApprove: (stepId: number, approved: boolean) => void;
}) {
  return (
    <div className="flex flex-col gap-4 py-2">
      {steps.map((step) => (
        <StepCard key={step.id} step={step} onApprove={onApprove} />
      ))}
      {status === "running" && (
        <div className="pl-4 flex items-center gap-2 text-muted text-xs font-mono">
          <span className="w-1.5 h-1.5 rounded-full bg-signal pulse" />
          agent is working…
        </div>
      )}
    </div>
  );
}
