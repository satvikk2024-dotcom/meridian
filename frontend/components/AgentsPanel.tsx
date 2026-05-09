"use client";

import { useEffect, useState } from "react";
import StatusBadge from "@/components/ui/StatusBadge";
import type { AgentState, CriticResult, RunStatus } from "@/lib/sse";
import type { BadgeStatus } from "@/components/ui/StatusBadge";

const AGENT_META: { key: string; label: string }[] = [
  { key: "financial", label: "Financial"         },
  { key: "market",    label: "Market"            },
  { key: "people",    label: "Leadership"        },
  { key: "customer",  label: "Sentiment"         },
];

function agentBadge(status: AgentState["status"]): BadgeStatus {
  switch (status) {
    case "pending":  return "pending";
    case "running":  return "running";
    case "complete": return "complete";
    case "failed":   return "failed";
  }
}

function formatMs(ms: number) {
  const s = ms / 1000;
  return s < 60 ? `${s.toFixed(1)}s` : `${Math.floor(s / 60)}m ${Math.floor(s % 60)}s`;
}

interface AgentRowProps {
  label: string;
  state: AgentState;
  selected: boolean;
  onClick: () => void;
}

function AgentRow({ label, state, selected, onClick }: AgentRowProps) {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    if (state.status !== "running") return;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [state.status]);

  const elapsed =
    state.finishedAt != null && state.startedAt != null
      ? formatMs(state.finishedAt - state.startedAt)
      : state.startedAt != null
      ? formatMs(now - state.startedAt)
      : null;

  const findingCount = Object.keys(state.findings).length;

  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors duration-100
        ${selected
          ? "bg-accent-dim border-l-2 border-accent"
          : "border-l-2 border-transparent hover:bg-bg-elevated"
        }`}
    >
      <StatusBadge status={agentBadge(state.status)} label="" className="flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p
          className={`font-mono truncate ${selected ? "text-fg-primary" : "text-fg-secondary"}`}
          style={{ fontSize: 13 }}
        >
          {label}
        </p>
        {findingCount > 0 && (
          <p className="font-mono text-fg-muted" style={{ fontSize: 11 }}>
            {findingCount} findings
          </p>
        )}
      </div>
      {elapsed && (
        <span className="font-mono text-fg-muted flex-shrink-0" style={{ fontSize: 11 }}>
          {elapsed}
        </span>
      )}
    </button>
  );
}

interface AgentsPanelProps {
  agents: Record<string, AgentState>;
  criticResult: CriticResult | null;
  runStatus: RunStatus;
  selectedAgent: string | null;
  onSelectAgent: (name: string | null) => void;
}

export default function AgentsPanel({
  agents,
  criticResult,
  runStatus,
  selectedAgent,
  onSelectAgent,
}: AgentsPanelProps) {
  const criticStatus: BadgeStatus = criticResult
    ? "complete"
    : runStatus === "complete"
    ? "complete"
    : runStatus === "running"
    ? "pending"
    : "pending";

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border-subtle">
        <span
          className="font-mono text-fg-muted tracking-widest uppercase"
          style={{ fontSize: 11 }}
        >
          Agents
        </span>
      </div>

      {/* Agent rows */}
      <div className="flex flex-col py-1">
        {AGENT_META.map(({ key, label }) => (
          <AgentRow
            key={key}
            label={label}
            state={agents[key] ?? {
              status: "pending", startedAt: null, finishedAt: null,
              findings: {}, citations: [], error: null,
            }}
            selected={selectedAgent === key}
            onClick={() => onSelectAgent(selectedAgent === key ? null : key)}
          />
        ))}
      </div>

      {/* Critic section */}
      <div className="mt-2 border-t border-border-subtle">
        <div className="px-4 py-3">
          <span
            className="font-mono text-fg-muted tracking-widest uppercase"
            style={{ fontSize: 11 }}
          >
            Critic
          </span>
        </div>
        <div className="px-4 pb-3 flex items-center gap-3">
          <StatusBadge status={criticStatus} label="" className="flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="font-mono text-fg-secondary" style={{ fontSize: 13 }}>
              Hallucination check
            </p>
            {criticResult && (
              <p className="font-mono text-fg-muted" style={{ fontSize: 11 }}>
                {Math.round(criticResult.hallucination_rate * 100)}% flagged
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
