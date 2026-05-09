/* Run page — M1 scaffold only. Real wiring happens in M3. */
export default function RunPage({ params }: { params: { id: string } }) {
  return (
    <div
      className="h-screen w-full overflow-hidden"
      style={{
        display: "grid",
        gridTemplateColumns: "280px 1fr 340px",
        gridTemplateRows: "1fr 40px",
        gridTemplateAreas: `
          "agents-panel main-panel context-rail"
          "event-log    event-log  event-log"
        `,
        background: "var(--bg-primary)",
      }}
    >
      {/* Left rail — agents */}
      <div
        style={{ gridArea: "agents-panel" }}
        className="border-r border-border-subtle flex items-center justify-center"
      >
        <span className="font-mono text-micro text-fg-muted tracking-widest uppercase">
          agents-panel
        </span>
      </div>

      {/* Center — memo / evidence / trace tabs */}
      <div
        style={{ gridArea: "main-panel" }}
        className="flex items-center justify-center"
      >
        <span className="font-mono text-micro text-fg-muted tracking-widest uppercase">
          main-panel · run/{params.id}
        </span>
      </div>

      {/* Right rail — context */}
      <div
        style={{ gridArea: "context-rail" }}
        className="border-l border-border-subtle flex items-center justify-center"
      >
        <span className="font-mono text-micro text-fg-muted tracking-widest uppercase">
          context-rail
        </span>
      </div>

      {/* Bottom — event log */}
      <div
        style={{ gridArea: "event-log" }}
        className="border-t border-border-subtle flex items-center px-4"
      >
        <span className="font-mono text-micro text-fg-muted tracking-widest uppercase">
          event-log
        </span>
      </div>
    </div>
  );
}
