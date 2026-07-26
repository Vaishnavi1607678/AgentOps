"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  approveStep,
  createRun,
  getRun,
  listRuns,
  RunSummary,
  StepRecord,
  streamRun,
} from "@/lib/api";
import RunList from "@/components/RunList";
import NewRunForm from "@/components/NewRunForm";
import MetricsBar from "@/components/MetricsBar";
import TraceTimeline from "@/components/TraceTimeline";

export default function Home() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [run, setRun] = useState<RunSummary | null>(null);
  const [steps, setSteps] = useState<StepRecord[]>([]);
  const [creating, setCreating] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const refreshRunList = useCallback(async () => {
    try {
      const data = await listRuns();
      setRuns(data);
    } catch {
      // backend not reachable yet — silently retry on next interval
    }
  }, []);

  useEffect(() => {
    refreshRunList();
    const interval = setInterval(refreshRunList, 4000);
    return () => clearInterval(interval);
  }, [refreshRunList]);

  useEffect(() => {
    if (selectedId == null) return;
    let active = true;
    getRun(selectedId).then(({ run, steps }) => {
      if (!active) return;
      setRun(run);
      setSteps(steps);
    });
    const unsubscribe = streamRun(selectedId, (event, data) => {
      if (event === "step") {
        setSteps((prev) => {
          const exists = prev.some((s) => s.id === data.id);
          const next = exists ? prev.map((s) => (s.id === data.id ? data : s)) : [...prev, data];
          return next.sort((a, b) => a.seq - b.seq);
        });
      }
      if (event === "run_status") {
        setRun((prev) => (prev ? { ...prev, status: data.status } : prev));
        refreshRunList();
      }
    });
    return () => {
      active = false;
      unsubscribe();
    };
  }, [selectedId, refreshRunList]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [steps]);

  async function handleCreateRun(task: string) {
    setCreating(true);
    try {
      const { run_id } = await createRun(task);
      await refreshRunList();
      setSelectedId(run_id);
    } finally {
      setCreating(false);
    }
  }

  async function handleApprove(stepId: number, approved: boolean) {
    setSteps((prev) => prev.map((s) => (s.id === stepId ? { ...s, type: approved ? "approval_granted" : "approval_denied" } : s)));
    await approveStep(stepId, approved);
  }

  return (
    <div className="flex h-screen">
      <aside className="w-72 border-r border-line flex flex-col shrink-0">
        <div className="px-5 py-4 border-b border-line">
          <h1 className="font-mono text-sm font-semibold tracking-tight text-ink">AgentOps</h1>
          <p className="text-[11px] text-muted mt-0.5">autonomous infra agent, observed</p>
        </div>
        <div className="overflow-y-auto flex-1">
          <RunList runs={runs} selectedId={selectedId} onSelect={setSelectedId} />
        </div>
      </aside>

      <main className="flex-1 flex flex-col min-w-0">
        <NewRunForm onSubmit={handleCreateRun} disabled={creating} />
        {run ? (
          <>
            <MetricsBar run={run} />
            <div className="flex-1 overflow-y-auto px-5">
              <TraceTimeline steps={steps} status={run.status} onApprove={handleApprove} />
              <div ref={bottomRef} />
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-muted text-sm">
            Select a run, or start a new one above.
          </div>
        )}
      </main>
    </div>
  );
}
