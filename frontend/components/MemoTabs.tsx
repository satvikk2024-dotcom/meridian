"use client";

import { useState } from "react";
import MemoViewer from "@/components/MemoViewer";
import EvidenceTab from "@/components/EvidenceTab";
import TraceTab from "@/components/TraceTab";
import type { AgentState, CriticResult, RawEvent, RawCitation } from "@/lib/sse";

type Tab = "memo" | "evidence" | "trace";

const TABS: { id: Tab; label: string }[] = [
  { id: "memo",     label: "Memo"     },
  { id: "evidence", label: "Evidence" },
  { id: "trace",    label: "Trace"    },
];

interface MemoTabsProps {
  memo: string | null;
  agents: Record<string, AgentState>;
  criticResult: CriticResult | null;
  events: RawEvent[];
}

export default function MemoTabs({ memo, agents, criticResult, events }: MemoTabsProps) {
  const [activeTab, setActiveTab] = useState<Tab>("memo");

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Tab bar */}
      <div className="flex items-end gap-0 border-b border-border-subtle px-4 flex-shrink-0">
        {TABS.map(({ id, label }) => {
          const isActive = activeTab === id;
          return (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`px-4 h-9 font-mono transition-colors relative
                ${isActive
                  ? "text-fg-primary"
                  : "text-fg-muted hover:text-fg-secondary"
                }`}
              style={{ fontSize: 12 }}
            >
              {label}
              {isActive && (
                <span
                  className="absolute bottom-0 left-0 right-0 h-px bg-accent"
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === "memo" && (
          <MemoViewer
            memo={memo}
            newsCitations={(agents.financial?.citations ?? []).filter(
              (c) => c.source === "news"
            )}
          />
        )}

        {activeTab === "evidence" && (
          <EvidenceTab agents={agents} />
        )}

        {activeTab === "trace" && (
          <TraceTab events={events} />
        )}
      </div>
    </div>
  );
}
