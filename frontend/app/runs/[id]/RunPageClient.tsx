"use client";

import { useState } from "react";
import { useRunEvents } from "@/lib/sse";
import RunHeader from "@/components/RunHeader";
import AgentsPanel from "@/components/AgentsPanel";
import MemoTabs from "@/components/MemoTabs";
import EventLog from "@/components/EventLog";
import ContextRail from "@/components/ContextRail";

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

      {/* Center — memo / evidence / trace */}
      <div
        style={{ gridArea: "main-panel" }}
        className="overflow-hidden"
      >
        {state.error ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 px-8 text-center">
            <p className="font-mono text-danger" style={{ fontSize: 13 }}>
              Connection lost
            </p>
            <p className="font-mono text-fg-muted" style={{ fontSize: 11 }}>
              {state.error}
            </p>
            <a
              href="/"
              className="mt-2 px-3 py-1.5 rounded font-mono border
                bg-bg-elevated border-border-default text-fg-secondary
                hover:border-accent hover:text-fg-primary transition-colors"
              style={{ fontSize: 12 }}
            >
              ← New run
            </a>
          </div>
        ) : (
          <MemoTabs
            memo={state.memo}
            agents={state.agents}
            criticResult={state.criticResult}
            events={state.events}
          />
        )}
      </div>

      {/* Right rail — stock snapshot */}
      <div
        style={{ gridArea: "context-rail" }}
        className="border-l border-border-subtle overflow-hidden"
      >
        <ContextRail
          agents={state.agents}
          criticResult={state.criticResult}
          ticker={ticker}
        />
      </div>

      {/* Bottom — event log */}
      <div
        style={{ gridArea: "event-log" }}
        className="border-t border-border-subtle overflow-hidden"
      >
        <EventLog events={state.events} status={state.status} />
      </div>
    </div>
  );
}
