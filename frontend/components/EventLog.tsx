"use client";

import { useEffect, useRef } from "react";
import type { RawEvent, RunStatus } from "@/lib/sse";

const EVENT_ACCENT: Record<string, string> = {
  run_started:   "text-accent",
  agent_started: "text-sky-400",
  agent_done:    "text-emerald-400",
  critic_done:   "text-violet-400",
  run_complete:  "text-accent",
};

function accent(type: string): string {
  return EVENT_ACCENT[type] ?? "text-fg-muted";
}

interface EventLogProps {
  events: RawEvent[];
  status: RunStatus;
}

export default function EventLog({ events, status }: EventLogProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest event
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollLeft = el.scrollWidth;
  }, [events.length]);

  return (
    <div className="flex items-center h-full gap-3 px-4 overflow-hidden">
      {/* Status label */}
      <span className="font-mono text-fg-muted flex-shrink-0" style={{ fontSize: 11 }}>
        {events.length > 0 ? `${events.length} events` : "idle"}
      </span>

      {/* Divider */}
      {events.length > 0 && (
        <span className="text-border-default flex-shrink-0" style={{ fontSize: 14 }}>
          ·
        </span>
      )}

      {/* Scrolling event ticker */}
      <div
        ref={scrollRef}
        className="flex items-center gap-2 overflow-x-auto flex-1 min-w-0"
        style={{ scrollbarWidth: "none" }}
      >
        {events.map((evt, i) => (
          <span
            key={i}
            className={`font-mono flex-shrink-0 ${accent(evt.type)}`}
            style={{ fontSize: 11 }}
          >
            {evt.type}
            {i < events.length - 1 && (
              <span className="text-border-default ml-2">→</span>
            )}
          </span>
        ))}
      </div>

      {/* Run status pill on far right */}
      {status === "running" && (
        <span
          className="font-mono text-accent flex-shrink-0 animate-pulse-accent"
          style={{ fontSize: 11 }}
        >
          live
        </span>
      )}
      {status === "complete" && (
        <span className="font-mono text-fg-muted flex-shrink-0" style={{ fontSize: 11 }}>
          done
        </span>
      )}
      {status === "failed" && (
        <span className="font-mono text-danger flex-shrink-0" style={{ fontSize: 11 }}>
          failed
        </span>
      )}
    </div>
  );
}
