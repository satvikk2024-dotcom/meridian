"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, AlertTriangle, ExternalLink, Newspaper } from "lucide-react";
import { parseMemo, type MemoSection, type MemoField } from "@/lib/memo";
import CitationCard from "@/components/CitationCard";
import type { RawCitation } from "@/lib/sse";

// ── Skeleton ─────────────────────────────────────────────────────────

function SkeletonBar({ w = "100%", h = 12 }: { w?: string; h?: number }) {
  return (
    <div
      className="rounded bg-bg-elevated animate-pulse"
      style={{ width: w, height: h }}
    />
  );
}

function MemoSkeleton() {
  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <SkeletonBar w="60%" h={20} />
        <SkeletonBar w="35%" h={12} />
      </div>
      {/* Three placeholder sections */}
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex flex-col gap-3 border border-border-subtle rounded-md p-4">
          <SkeletonBar w="40%" h={14} />
          <SkeletonBar w="90%" />
          <SkeletonBar w="75%" />
          <SkeletonBar w="82%" />
          <SkeletonBar w="65%" />
        </div>
      ))}
    </div>
  );
}

// ── Field renderer ────────────────────────────────────────────────────

function FieldRow({ field }: { field: MemoField }) {
  return (
    <div className="py-2 border-b border-border-subtle last:border-0">
      {/* Label row */}
      <div className="flex items-center gap-2 mb-1">
        <span className="font-mono text-fg-muted" style={{ fontSize: 11 }}>
          {field.label}
        </span>
        {field.flagged && (
          <span
            className="flex items-center gap-1 font-mono"
            style={{ fontSize: 10, color: "var(--warning)" }}
            title="Critic: limited evidence"
          >
            <AlertTriangle size={10} />
            unverified
          </span>
        )}
      </div>

      {/* Value */}
      {field.isList ? (
        <ul className="flex flex-col gap-1">
          {field.items.map((item, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="text-fg-muted flex-shrink-0 mt-px" style={{ fontSize: 11 }}>
                —
              </span>
              <span className="font-mono text-fg-secondary" style={{ fontSize: 12 }}>
                {item}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="font-mono text-fg-secondary" style={{ fontSize: 12 }}>
          {field.value || <span className="text-fg-muted italic">—</span>}
        </p>
      )}
    </div>
  );
}

// ── Section card ──────────────────────────────────────────────────────

function SectionCard({
  section,
  defaultOpen,
}: {
  section: MemoSection;
  defaultOpen: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const flagCount = section.fields.filter((f) => f.flagged).length;

  return (
    <div className="border border-border-subtle rounded-md overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3
          bg-bg-surface hover:bg-bg-elevated transition-colors"
      >
        <div className="flex items-center gap-3">
          {open ? (
            <ChevronDown size={13} className="text-fg-muted" />
          ) : (
            <ChevronRight size={13} className="text-fg-muted" />
          )}
          <span className="font-mono text-fg-primary" style={{ fontSize: 13 }}>
            {section.title}
          </span>
          <span className="font-mono text-fg-muted" style={{ fontSize: 11 }}>
            {section.fields.length} fields
          </span>
        </div>
        {flagCount > 0 && (
          <span
            className="font-mono flex items-center gap-1"
            style={{ fontSize: 10, color: "var(--warning)" }}
          >
            <AlertTriangle size={10} />
            {flagCount} flagged
          </span>
        )}
      </button>

      {/* Fields */}
      {open && (
        <div className="px-4 py-1 bg-bg-primary">
          {section.fields.length === 0 ? (
            <p className="font-mono text-fg-muted py-3" style={{ fontSize: 11 }}>
              No data available
            </p>
          ) : (
            section.fields.map((field, i) => <FieldRow key={i} field={field} />)
          )}
        </div>
      )}
    </div>
  );
}

// ── News card ─────────────────────────────────────────────────────────

function NewsCard({ items }: { items: RawCitation[] }) {
  if (items.length === 0) return null;

  return (
    <div className="border border-border-subtle rounded-md overflow-hidden">
      <div className="px-4 py-3 bg-bg-surface flex items-center gap-2">
        <Newspaper size={12} className="text-cyan-400" />
        <span className="font-mono text-fg-muted" style={{ fontSize: 11 }}>
          RECENT NEWS · {items.length}
        </span>
      </div>
      <div className="bg-bg-primary divide-y divide-border-subtle">
        {items.map((item, i) => {
          const date = item.fetched_at
            ? new Date(item.fetched_at).toLocaleDateString("en-IN", {
                day: "numeric", month: "short", year: "numeric",
              })
            : "";
          return (
            <a
              key={i}
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-start gap-3 px-4 py-3 hover:bg-bg-elevated transition-colors group"
            >
              <div className="flex-1 min-w-0">
                <p className="font-mono text-fg-primary group-hover:text-accent transition-colors"
                   style={{ fontSize: 12, lineHeight: 1.5 }}>
                  {item.label}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="font-mono px-1.5 py-0.5 rounded text-cyan-400 bg-cyan-400/10"
                        style={{ fontSize: 10 }}>
                    {item.value}
                  </span>
                  {date && (
                    <span className="font-mono text-fg-muted" style={{ fontSize: 10 }}>
                      {date}
                    </span>
                  )}
                </div>
              </div>
              <ExternalLink size={12} className="text-fg-muted group-hover:text-accent flex-shrink-0 mt-1 transition-colors" />
            </a>
          );
        })}
      </div>
    </div>
  );
}

// ── Main viewer ───────────────────────────────────────────────────────

interface MemoViewerProps {
  memo: string | null;
  newsCitations?: RawCitation[];
}

export default function MemoViewer({ memo, newsCitations = [] }: MemoViewerProps) {
  if (!memo) {
    return (
      <div className="h-full overflow-y-auto">
        <MemoSkeleton />
        {newsCitations.length > 0 && (
          <div className="max-w-2xl mx-auto px-6 pb-6">
            <NewsCard items={newsCitations} />
          </div>
        )}
      </div>
    );
  }

  const parsed = parseMemo(memo);

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-2xl mx-auto px-6 py-6 flex flex-col gap-4">
        {/* Header */}
        <div className="flex flex-col gap-1 pb-2 border-b border-border-subtle">
          <h2 className="font-mono text-fg-primary" style={{ fontSize: 16 }}>
            {parsed.title || "Due Diligence Report"}
          </h2>
          {parsed.generatedAt && (
            <p className="font-mono text-fg-muted" style={{ fontSize: 11 }}>
              Generated {parsed.generatedAt}
            </p>
          )}
        </div>

        {/* Sections */}
        {parsed.sections.map((section, i) => (
          <SectionCard
            key={section.title}
            section={section}
            defaultOpen={i < 3}
          />
        ))}

        {/* Recent News */}
        <NewsCard items={newsCitations} />

        {/* Citations */}
        {parsed.citations.length > 0 && (
          <div className="border border-border-subtle rounded-md overflow-hidden">
            <div className="px-4 py-3 bg-bg-surface">
              <span className="font-mono text-fg-muted" style={{ fontSize: 11 }}>
                CITATIONS · {parsed.citations.length}
              </span>
            </div>
            <div className="px-4 py-2 bg-bg-primary">
              {parsed.citations.map((c) => (
                <CitationCard key={c.idx} citation={c} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
