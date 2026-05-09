"use client";

import { ExternalLink } from "lucide-react";
import type { MemoCitation } from "@/lib/memo";

const SOURCE_COLORS: Record<string, string> = {
  yfinance:  "text-blue-400  bg-blue-400/10",
  wikipedia: "text-slate-400 bg-slate-400/10",
  reddit:    "text-orange-400 bg-orange-400/10",
  github:    "text-purple-400 bg-purple-400/10",
  news:      "text-cyan-400  bg-cyan-400/10",
};

function sourceClass(source: string): string {
  return SOURCE_COLORS[source.toLowerCase()] ?? "text-fg-muted bg-bg-elevated";
}

interface CitationCardProps {
  citation: MemoCitation;
}

export default function CitationCard({ citation }: CitationCardProps) {
  const { idx, source, label, value, url } = citation;

  return (
    <div className="flex items-start gap-3 py-2 border-b border-border-subtle last:border-0">
      {/* Index */}
      <span
        className="font-mono text-fg-muted flex-shrink-0 w-5 text-right"
        style={{ fontSize: 11 }}
      >
        {idx}.
      </span>

      {/* Source badge */}
      <span
        className={`font-mono flex-shrink-0 px-1.5 py-0.5 rounded text-micro ${sourceClass(source)}`}
      >
        {source}
      </span>

      {/* Label + value */}
      <div className="flex-1 min-w-0">
        <span className="font-mono text-fg-secondary" style={{ fontSize: 12 }}>
          {label}
        </span>
        {value && (
          <span className="font-mono text-fg-muted" style={{ fontSize: 12 }}>
            {": "}
            {value.length > 80 ? value.slice(0, 80) + "…" : value}
          </span>
        )}
      </div>

      {/* URL link */}
      {url && (
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-shrink-0 text-fg-muted hover:text-accent transition-colors"
          title={url}
        >
          <ExternalLink size={12} />
        </a>
      )}
    </div>
  );
}
