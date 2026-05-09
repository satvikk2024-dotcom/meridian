"use client";

import { useState } from "react";
import { useRunEvents } from "@/lib/sse";
import RunHeader from "@/components/RunHeader";
import AgentsPanel from "@/components/AgentsPanel";

interface RunPageClientProps {
  company: string;
  ticker: string;
}

export default function RunPageClient({ company, ticker }: RunPageClientProps) {
  const state = useRunEvents(company, ticker);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  const missingTicker = !ticker;

  if (missingTicker) {
    return (
      <div className="flex h-screen items-center justify-center bg-bg-primary">
        <div className="flex flex-col items-center gap-4 text-center px-8">
          <p className="font-mono text-fg-primary" style={{ fontSize: 18 }}>
            Ticker required
          </p>
          <p className="font-mono text-fg-muted" style={{ fontSize: 13 }}>
            Use one of the demo company chips on the landing page,
            or append{" "}
            <code className="text-accent">?ticker=SYMBOL.NS</code>{" "}
            to the URL.
          </p>
          <a
            href="/"
            className="mt-2 px-4 py-2 rounded-md font-mono text-small
              bg-bg-elevated border border-border-default text-fg-secondary
              hover:border-accent hover:text-fg-primary transition-colors"
          >
            ← Back
          </a>
        </div>
      </div>
    );
  }

  return (
    <div
      className="h-screen w-full overflow-hidden bg-bg-primary"
      style={{
        display: "grid",
        gridTemplateColumns: "280px 1fr 340px",
        gridTemplateRows: "64px 1fr 40px",
        gridTemplateAreas: `
          "header      header      header"
          "agents-panel main-panel context-rail"
          "event-log   event-log   event-log"
        `,
      }}
    >
      {/* Header — spans full width */}
      <div style={{ gridArea: "header" }}>
        <RunHeader
          company={company}
          status={state.status}
          startedAt={state.startedAt}
          duration={state.duration}
        />
      </div>

      {/* Left rail — agents */}
      <div
        style={{ gridArea: "agents-panel" }}
        className="border-r border-border-subtle overflow-hidden"
      >
        <AgentsPanel
          agents={state.agents}
          criticResult={state.criticResult}
          runStatus={state.status}
          selectedAgent={selectedAgent}
          onSelectAgent={setSelectedAgent}
        />
      </div>

      {/* Center — memo / evidence / trace (M4) */}
      <div
        style={{ gridArea: "main-panel" }}
        className="flex items-center justify-center"
      >
        <span className="font-mono text-fg-muted" style={{ fontSize: 11 }}>
          {state.status === "complete"
            ? "memo ready — coming in M4"
            : state.status === "running"
            ? "agents running…"
            : "waiting to start"}
        </span>
      </div>

      {/* Right rail — context (M8) */}
      <div
        style={{ gridArea: "context-rail" }}
        className="border-l border-border-subtle flex items-center justify-center"
      >
        <span className="font-mono text-fg-muted" style={{ fontSize: 11 }}>
          context-rail
        </span>
      </div>

      {/* Bottom — event log (M6) */}
      <div
        style={{ gridArea: "event-log" }}
        className="border-t border-border-subtle flex items-center gap-3 px-4"
      >
        <span className="font-mono text-fg-muted" style={{ fontSize: 11 }}>
          {state.events.length > 0
            ? `${state.events.length} events`
            : "event-log — M6"}
        </span>
        {state.events.length > 0 && (
          <span className="font-mono text-fg-muted" style={{ fontSize: 11 }}>
            · last:{" "}
            <span className="text-accent">
              {state.events[state.events.length - 1]?.type}
            </span>
          </span>
        )}
      </div>
    </div>
  );
}
