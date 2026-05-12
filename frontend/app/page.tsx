import { ExternalLink } from "lucide-react";
import RunForm from "@/components/RunForm";

export default function Home() {
  return (
    <main
      className="relative flex flex-col min-h-screen bg-bg-primary overflow-hidden"
    >
      {/* ── Dot-grid background ───────────────────────────────────── */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            "radial-gradient(circle, var(--border-default) 1px, transparent 1px)",
          backgroundSize: "28px 28px",
          opacity: 0.6,
        }}
      />

      {/* ── Top bar ──────────────────────────────────────────────── */}
      <header className="relative z-10 flex items-center justify-between px-8 h-16 border-b border-border-subtle">
        <span
          className="font-mono text-accent font-bold tracking-[0.35em] uppercase"
          style={{ fontSize: 22 }}
        >
          Meridian
        </span>
        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="GitHub"
          className="text-fg-muted hover:text-fg-primary transition-colors duration-150"
        >
          <ExternalLink size={16} />
        </a>
      </header>

      {/* ── Center content ───────────────────────────────────────── */}
      <section className="relative z-10 flex flex-1 flex-col items-center justify-center gap-8 px-4">
        {/* Headline */}
        <div className="flex flex-col items-center gap-2 text-center">
          <h1
            className="font-mono text-fg-primary font-semibold tracking-tight"
            style={{ fontSize: 32 }}
          >
            Due diligence,{" "}
            <span className="text-accent">automated.</span>
          </h1>
          <p className="text-fg-muted" style={{ fontSize: 15 }}>
            Multi-agent research on any public company in minutes.
          </p>
          <p className="font-mono text-fg-muted tracking-[0.2em] uppercase" style={{ fontSize: 11, marginTop: 6 }}>
            —— Satvik Krishna ——
          </p>
        </div>

        {/* Run form */}
        <RunForm />
      </section>

      {/* ── Bottom stats ─────────────────────────────────────────── */}
      {/*
        GET /api/stats does not exist yet on the backend.
        Showing static placeholder text. Will wire up in Phase 9 or 10.
      */}
      <footer className="relative z-10 flex items-center justify-center h-12 border-t border-border-subtle">
        <span className="font-mono text-fg-muted" style={{ fontSize: 11 }}>
          multi-agent · citation-grounded · critic-scored
        </span>
      </footer>
    </main>
  );
}
