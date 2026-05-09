"use client";

import type { RawEvent } from "@/lib/sse";

const EVENT_COLORS: Record<string, string> = {
  run_started:   "text-accent",
  agent_started: "text-sky-400",
  agent_done:    "text-emerald-400",
  critic_done:   "text-violet-400",
  run_complete:  "text-accent",
  error:         "text-danger",
};

function eventColor(type: string): string {
  return EVENT_COLORS[type] ?? "text-fg-muted";
}

function formatTs(ts: number, baseTs: number): string {
  const delta = (ts - baseTs) / 1000;
  return `+${delta.toFixed(2)}s`;
}

function payloadPreview(data: Record<string, unknown>): string {
  const keys = Object.keys(data).filter((k) => k !== "memo"); // memo is huge
  const pairs = keys.slice(0, 3).map((k) => {
    const v = data[k];
    const display =
      typeof v === "string"
        ? v.length > 24 ? v.slice(0, 24) + "…" : v
        : typeof v === "number"
        ? String(v)
        : Array.isArray(v)
        ? `[${v.length}]`
        : typeof v === "object" && v !== null
        ? "{…}"
        : String(v);
    return `${k}: ${display}`;
  });
  if (keys.length > 3) pairs.push(`+${keys.length - 3} more`);
  return pairs.join("  ·  ");
}

interface TraceTabProps {
  events: RawEvent[];
}

export default function TraceTab({ events }: TraceTabProps) {
  if (events.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <span className="font-mono text-fg-muted" style={{ fontSize: 11 }}>
          Waiting for events…
        </span>
      </div>
    );
  }

  const baseTs = events[0].ts;

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-4 py-3 flex flex-col gap-0">
        {events.map((evt, i) => (
          <div
            key={i}
            className="flex items-start gap-3 py-2 border-b border-border-subtle last:border-0"
          >
            {/* Relative timestamp */}
            <span
              className="font-mono text-fg-muted flex-shrink-0 w-12 text-right"
              style={{ fontSize: 11 }}
            >
              {formatTs(evt.ts, baseTs)}
            </span>

            {/* Event type */}
            <span
              className={`font-mono flex-shrink-0 w-32 ${eventColor(evt.type)}`}
              style={{ fontSize: 12 }}
            >
              {evt.type}
            </span>

            {/* Payload preview */}
            <span
              className="font-mono text-fg-muted flex-1 min-w-0 truncate"
              style={{ fontSize: 11 }}
            >
              {payloadPreview(evt.data)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
