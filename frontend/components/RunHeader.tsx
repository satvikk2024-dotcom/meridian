"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus } from "lucide-react";
import StatusBadge, { BadgeStatus } from "@/components/ui/StatusBadge";
import type { RunStatus } from "@/lib/sse";

function statusToBadge(status: RunStatus): BadgeStatus {
  switch (status) {
    case "idle":     return "pending";
    case "running":  return "running";
    case "complete": return "complete";
    case "failed":   return "failed";
  }
}

function formatElapsed(ms: number): string {
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}

interface RunHeaderProps {
  company: string;
  status: RunStatus;
  startedAt: number | null;
  duration: number | null;
}

export default function RunHeader({ company, status, startedAt, duration }: RunHeaderProps) {
  const router = useRouter();
  const [now, setNow] = useState(Date.now());

  // Tick every second while running
  useEffect(() => {
    if (status !== "running") return;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [status]);

  const elapsed =
    duration != null
      ? `${duration}s`
      : startedAt != null
      ? formatElapsed(now - startedAt)
      : null;

  return (
    <div className="flex items-center justify-between px-6 h-16 border-b border-border-subtle flex-shrink-0">
      {/* Left: company + status */}
      <div className="flex flex-col gap-1">
        <h1
          className="text-fg-primary font-semibold leading-none truncate"
          style={{ fontSize: 18 }}
        >
          {company || "Loading…"}
        </h1>
        <div className="flex items-center gap-3">
          <StatusBadge status={statusToBadge(status)} />
          {elapsed && (
            <span className="font-mono text-fg-muted" style={{ fontSize: 11 }}>
              {elapsed}
            </span>
          )}
        </div>
      </div>

      {/* Right: new run button */}
      <button
        onClick={() => router.push("/")}
        className="flex items-center gap-1 px-3 h-8 rounded-md font-mono
          bg-bg-elevated text-fg-secondary border border-border-default
          hover:border-accent hover:text-fg-primary
          transition-colors duration-150 flex-shrink-0"
        style={{ fontSize: 12 }}
      >
        <Plus size={13} />
        New run
      </button>
    </div>
  );
}
