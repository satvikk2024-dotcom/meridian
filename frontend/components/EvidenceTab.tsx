"use client";

import { useState, useMemo } from "react";
import { ExternalLink } from "lucide-react";
import type { AgentState } from "@/lib/sse";

interface EvidenceRow {
  agent: string;
  agentLabel: string;
  source: string;
  label: string;
  value: string;
  url: string | null;
}

const AGENT_LABELS: Record<string, string> = {
  financial: "Financial",
  market:    "Market",
  people:    "Leadership",
  customer:  "Sentiment",
};

const SOURCE_COLORS: Record<string, string> = {
  yfinance:  "text-blue-400  bg-blue-400/10  border-blue-400/20",
  wikipedia: "text-slate-400 bg-slate-400/10 border-slate-400/20",
  reddit:    "text-orange-400 bg-orange-400/10 border-orange-400/20",
  github:    "text-purple-400 bg-purple-400/10 border-purple-400/20",
  news:      "text-cyan-400  bg-cyan-400/10  border-cyan-400/20",
};

const AGENT_COLORS: Record<string, string> = {
  financial: "text-emerald-400 bg-emerald-400/10",
  market:    "text-sky-400    bg-sky-400/10",
  people:    "text-violet-400 bg-violet-400/10",
  customer:  "text-amber-400  bg-amber-400/10",
};

function sourceClass(source: string): string {
  return SOURCE_COLORS[source.toLowerCase()] ?? "text-fg-muted bg-bg-elevated border-border-subtle";
}

function agentClass(agent: string): string {
  return AGENT_COLORS[agent] ?? "text-fg-muted bg-bg-elevated";
}

interface FilterChipProps {
  label: string;
  active: boolean;
  count?: number;
  onClick: () => void;
}

function FilterChip({ label, active, count, onClick }: FilterChipProps) {
  return (
    <button
      onClick={onClick}
      className={`font-mono px-2 py-1 rounded text-micro border transition-colors
        ${active
          ? "bg-accent-dim border-accent text-accent"
          : "bg-bg-elevated border-border-default text-fg-muted hover:text-fg-secondary hover:border-border-default"
        }`}
    >
      {label}
      {count !== undefined && (
        <span className="ml-1 opacity-60">{count}</span>
      )}
    </button>
  );
}

interface EvidenceTabProps {
  agents: Record<string, AgentState>;
}

export default function EvidenceTab({ agents }: EvidenceTabProps) {
  const [agentFilter, setAgentFilter] = useState<string>("all");
  const [sourceFilter, setSourceFilter] = useState<string>("all");

  // Flatten all citations across agents into EvidenceRows
  const allRows = useMemo<EvidenceRow[]>(() => {
    const rows: EvidenceRow[] = [];
    for (const [agentKey, state] of Object.entries(agents)) {
      for (const raw of state.citations) {
        const c = raw as { source: string; label: string; value: string; url?: string };
        rows.push({
          agent:      agentKey,
          agentLabel: AGENT_LABELS[agentKey] ?? agentKey,
          source:     c.source ?? "unknown",
          label:      c.label  ?? "",
          value:      c.value  ?? "",
          url:        c.url    ?? null,
        });
      }
    }
    return rows;
  }, [agents]);

  // Unique agents and sources that actually have data
  const activeAgents = useMemo(
    () => Array.from(new Set(allRows.map((r) => r.agent))),
    [allRows]
  );
  const activeSources = useMemo(
    () => Array.from(new Set(allRows.map((r) => r.source))),
    [allRows]
  );

  const filtered = useMemo(
    () =>
      allRows.filter(
        (r) =>
          (agentFilter === "all" || r.agent === agentFilter) &&
          (sourceFilter === "all" || r.source === sourceFilter)
      ),
    [allRows, agentFilter, sourceFilter]
  );

  if (allRows.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <span className="font-mono text-fg-muted" style={{ fontSize: 11 }}>
          {Object.values(agents).some((a) => a.status === "running")
            ? "Collecting evidence…"
            : "No evidence collected"}
        </span>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Filter bar */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-border-subtle flex flex-wrap gap-2">
        {/* Agent filters */}
        <div className="flex items-center gap-1">
          <FilterChip
            label="All agents"
            active={agentFilter === "all"}
            count={agentFilter === "all" ? allRows.length : undefined}
            onClick={() => setAgentFilter("all")}
          />
          {activeAgents.map((key) => (
            <FilterChip
              key={key}
              label={AGENT_LABELS[key] ?? key}
              active={agentFilter === key}
              count={allRows.filter((r) => r.agent === key).length}
              onClick={() => setAgentFilter(agentFilter === key ? "all" : key)}
            />
          ))}
        </div>

        {/* Divider */}
        <span className="text-border-default" style={{ fontSize: 16 }}>|</span>

        {/* Source filters */}
        <div className="flex items-center gap-1">
          <FilterChip
            label="All sources"
            active={sourceFilter === "all"}
            onClick={() => setSourceFilter("all")}
          />
          {activeSources.map((src) => (
            <FilterChip
              key={src}
              label={src}
              active={sourceFilter === src}
              count={allRows.filter((r) => r.source === src).length}
              onClick={() => setSourceFilter(sourceFilter === src ? "all" : src)}
            />
          ))}
        </div>

        {/* Row count */}
        <span className="ml-auto font-mono text-fg-muted self-center" style={{ fontSize: 11 }}>
          {filtered.length} of {allRows.length}
        </span>
      </div>

      {/* Evidence list */}
      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 ? (
          <div className="flex items-center justify-center h-32">
            <span className="font-mono text-fg-muted" style={{ fontSize: 11 }}>
              No results for this filter
            </span>
          </div>
        ) : (
          <div className="divide-y divide-border-subtle">
            {filtered.map((row, i) => (
              <div
                key={i}
                className="flex items-start gap-3 px-4 py-3 hover:bg-bg-surface transition-colors"
              >
                {/* Source badge */}
                <span
                  className={`font-mono flex-shrink-0 px-1.5 py-0.5 rounded border text-micro ${sourceClass(row.source)}`}
                >
                  {row.source}
                </span>

                {/* Label + value */}
                <div className="flex-1 min-w-0">
                  <p className="font-mono text-fg-secondary" style={{ fontSize: 12 }}>
                    {row.label}
                  </p>
                  <p
                    className="font-mono text-fg-muted mt-0.5 break-words"
                    style={{ fontSize: 11 }}
                  >
                    {row.value.length > 140
                      ? row.value.slice(0, 140) + "…"
                      : row.value}
                  </p>
                </div>

                {/* Agent tag */}
                <span
                  className={`font-mono flex-shrink-0 px-1.5 py-0.5 rounded text-micro ${agentClass(row.agent)}`}
                >
                  {row.agentLabel}
                </span>

                {/* URL */}
                {row.url && (
                  <a
                    href={row.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-shrink-0 text-fg-muted hover:text-accent transition-colors mt-0.5"
                    title={row.url}
                  >
                    <ExternalLink size={12} />
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
