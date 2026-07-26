"use client";
import { useState } from "react";

const EXAMPLES = [
  "Investigate why checkout-service is slow and fix it",
  "Check the health of all services and report anything unusual",
  "Roll checkout-service back to the previous version",
];

export default function NewRunForm({ onSubmit, disabled }: { onSubmit: (task: string) => void; disabled: boolean }) {
  const [task, setTask] = useState("");

  function submit() {
    if (!task.trim() || disabled) return;
    onSubmit(task.trim());
    setTask("");
  }

  return (
    <div className="border-b border-line px-5 py-4">
      <div className="flex gap-2">
        <input
          value={task}
          onChange={(e) => setTask(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder="Give the agent a task…"
          className="flex-1 bg-surface border border-line rounded-md px-3 py-2 text-sm text-ink placeholder:text-muted font-mono focus:outline-none focus:border-signal/60 focus:ring-1 focus:ring-signal/30"
        />
        <button
          onClick={submit}
          disabled={disabled || !task.trim()}
          className="px-4 py-2 rounded-md bg-signal text-base font-medium text-sm hover:bg-signal/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          Run
        </button>
      </div>
      <div className="flex flex-wrap gap-1.5 mt-2.5">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => setTask(ex)}
            className="text-[11px] font-mono text-muted border border-line rounded-full px-2.5 py-1 hover:text-ink hover:border-signal/40 transition-colors"
          >
            {ex}
          </button>
        ))}
      </div>
    </div>
  );
}
