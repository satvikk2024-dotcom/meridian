"use client";

import type { AgentState, CriticResult } from "@/lib/sse";

// ── Helpers ───────────────────────────────────────────────────────────

function findCitation(citations: unknown[], label: string): string | null {
  for (const c of citations) {
    const { label: l, value: v } = c as { label: string; value: string };
    if (l === label) return v ?? null;
  }
  return null;
}

function parseNum(val: string | null): number | null {
  if (!val) return null;
  const m = val.replace(/[₹,]/g, "").match(/[\d.]+/);
  return m ? parseFloat(m[0]) : null;
}

function parse52W(val: string | null): { high: number; low: number } | null {
  if (!val) return null;
  // "₹1611.8 / ₹1290.0"
  const m = val.replace(/₹/g, "").match(/([\d,.]+)\s*\/\s*([\d,.]+)/);
  if (!m) return null;
  return {
    high: parseFloat(m[1].replace(/,/g, "")),
    low:  parseFloat(m[2].replace(/,/g, "")),
  };
}

function rangePos(price: number, low: number, high: number): number {
  if (high <= low) return 50;
  return Math.min(100, Math.max(0, ((price - low) / (high - low)) * 100));
}

function ratingColor(rating: string | null): string {
  if (!rating) return "text-fg-muted";
  const r = rating.toLowerCase();
  if (r.includes("strong_buy") || r.includes("buy")) return "text-accent";
  if (r.includes("hold"))                               return "text-warning";
  if (r.includes("sell"))                               return "text-danger";
  return "text-fg-secondary";
}

// ── Sub-components ────────────────────────────────────────────────────

function Skeleton() {
  return (
    <div className="h-3 rounded bg-bg-elevated animate-pulse w-3/4" />
  );
}

function MetricRow({
  label,
  value,
  loading,
  valueClass,
}: {
  label: string;
  value: string | null;
  loading: boolean;
  valueClass?: string;
}) {
  return (
    <div className="flex flex-col gap-1 py-2 border-b border-border-subtle last:border-0">
      <span className="font-mono text-fg-muted" style={{ fontSize: 10 }}>
        {label}
      </span>
      {loading && !value ? (
        <Skeleton />
      ) : (
        <span
          className={`font-mono ${valueClass ?? "text-fg-secondary"}`}
          style={{ fontSize: 12 }}
        >
          {value ?? "—"}
        </span>
      )}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────

interface ContextRailProps {
  agents:       Record<string, AgentState>;
  criticResult: CriticResult | null;
  ticker:       string;
}

export default function ContextRail({ agents, criticResult, ticker }: ContextRailProps) {
  const financial = agents.financial;
  const market    = agents.market;

  const finCits = financial?.citations ?? [];
  const mktCits = market?.citations    ?? [];

  const finLoading = financial?.status === "pending" || financial?.status === "running";
  const mktLoading = market?.status    === "pending" || market?.status    === "running";

  // Market data
  const priceRaw    = findCitation(mktCits, "Current Price");
  const weekRaw     = findCitation(mktCits, "52W High/Low");
  const ratingRaw   = findCitation(mktCits, "Analyst Rating");
  const price       = parseNum(priceRaw);
  const week        = parse52W(weekRaw);

  // Financial data
  const marketCap   = findCitation(finCits, "Market Cap");
  const revenue     = findCitation(finCits, "Revenue (TTM)");
  const netIncome   = findCitation(finCits, "Net Income (TTM)");
  const pe          = findCitation(finCits, "P/E Ratio");

  // Critic
  const hallucinationPct = criticResult
    ? Math.round(criticResult.hallucination_rate * 100)
    : null;

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border-subtle flex-shrink-0">
        <p className="font-mono text-fg-primary font-semibold" style={{ fontSize: 13 }}>
          {ticker || "—"}
        </p>
        <p className="font-mono text-fg-muted" style={{ fontSize: 10 }}>
          NSE / BSE
        </p>
      </div>

      {/* Price block */}
      <div className="px-4 py-3 border-b border-border-subtle flex-shrink-0">
        <p className="font-mono text-fg-muted" style={{ fontSize: 10 }}>
          CURRENT PRICE
        </p>
        {mktLoading && !priceRaw ? (
          <div className="mt-1 h-6 w-28 rounded bg-bg-elevated animate-pulse" />
        ) : (
          <p className="font-mono text-fg-primary font-semibold mt-1" style={{ fontSize: 20 }}>
            {priceRaw ?? "—"}
          </p>
        )}

        {/* 52W range bar */}
        {week && price ? (
          <div className="mt-3">
            <div className="flex justify-between font-mono text-fg-muted mb-1" style={{ fontSize: 9 }}>
              <span>52W L {week.low.toLocaleString()}</span>
              <span>H {week.high.toLocaleString()}</span>
            </div>
            <div className="relative h-1 rounded-full bg-bg-elevated">
              <div
                className="absolute top-0 h-1 rounded-full bg-border-default"
                style={{ width: "100%" }}
              />
              {/* Current price marker */}
              <div
                className="absolute top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-accent flex-shrink-0"
                style={{ left: `calc(${rangePos(price, week.low, week.high)}% - 4px)` }}
              />
            </div>
          </div>
        ) : mktLoading ? (
          <div className="mt-3 h-3 rounded bg-bg-elevated animate-pulse" />
        ) : null}
      </div>

      {/* Metrics */}
      <div className="px-4 flex-shrink-0">
        <MetricRow label="MARKET CAP"     value={marketCap}  loading={finLoading} />
        <MetricRow label="REVENUE (TTM)"  value={revenue}    loading={finLoading} />
        <MetricRow label="NET INCOME"     value={netIncome}  loading={finLoading} />
        <MetricRow label="P/E RATIO"      value={pe}         loading={finLoading} />
        <MetricRow
          label="ANALYST RATING"
          value={ratingRaw ? ratingRaw.replace(/_/g, " ").toUpperCase() : null}
          loading={mktLoading}
          valueClass={ratingColor(ratingRaw)}
        />
      </div>

      {/* Critic section */}
      <div className="px-4 py-3 border-t border-border-subtle mt-auto flex-shrink-0">
        <p className="font-mono text-fg-muted" style={{ fontSize: 10 }}>
          CRITIC SCORE
        </p>
        {criticResult === null ? (
          <div className="mt-1 h-3 w-20 rounded bg-bg-elevated animate-pulse" />
        ) : (
          <>
            <p
              className={`font-mono font-semibold mt-1 ${
                hallucinationPct! > 40 ? "text-danger" :
                hallucinationPct! > 20 ? "text-warning" : "text-accent"
              }`}
              style={{ fontSize: 16 }}
            >
              {100 - hallucinationPct!}%
            </p>
            <p className="font-mono text-fg-muted" style={{ fontSize: 10 }}>
              findings verified
            </p>
            {/* Bar */}
            <div className="mt-2 h-1 rounded-full bg-bg-elevated overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ${
                  hallucinationPct! > 40 ? "bg-danger" :
                  hallucinationPct! > 20 ? "bg-warning" : "bg-accent"
                }`}
                style={{ width: `${100 - hallucinationPct!}%` }}
              />
            </div>
            {criticResult.flagged_agents.length > 0 && (
              <p className="font-mono text-fg-muted mt-2" style={{ fontSize: 10 }}>
                Flagged: {criticResult.flagged_agents.join(", ")}
              </p>
            )}
          </>
        )}
      </div>

      {/* Source note */}
      <div className="px-4 pb-3 flex-shrink-0">
        <p className="font-mono text-fg-muted" style={{ fontSize: 9 }}>
          Data: yfinance · Not financial advice
        </p>
      </div>
    </div>
  );
}
