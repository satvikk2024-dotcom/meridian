# ADR-003: Use Server-Sent Events (not WebSockets) for progress streaming

## Status
Accepted — 2026-05

## Context

The frontend needs to display agent progress in real time as a Meridian run executes.
The data flow is **one-way**: the server pushes events to the client; the client never
needs to push back to the server during a run.

Options:

- **Server-Sent Events (SSE)** — One-way, server → client, over a long-lived HTTP response.
  Built-in browser API (`EventSource`); auto-reconnect.
- **WebSockets** — Bidirectional, full-duplex, persistent. Custom protocol on HTTP upgrade.
- **Polling** — Client repeatedly asks server "what's new?"

## Decision

Use SSE.

## Reasoning

- Our data flow is one-way; bidirectional WebSockets would be solving a problem we don't have.
- SSE is just an HTTP response with `Content-Type: text/event-stream`. No upgrade handshake,
  no special infrastructure, works through any HTTP proxy or CDN.
- The browser's built-in `EventSource` API handles reconnection, parsing, and error events for free.
- Polling wastes requests, increases latency, and creates worse UX.

## Consequences

**Positive:**
- One-line client code: `new EventSource(url).onmessage = ...`
- No special server setup; FastAPI supports SSE via `StreamingResponse` natively.
- Auto-reconnect built into the protocol.

**Negative:**
- One-way only. If we later need client → server real-time messaging (e.g., interactive
  agent steering), we'd need to add WebSockets or a separate POST endpoint.
- Some old proxy software buffers SSE. Not a concern for our hosting choices.

## Migration Path

If real-time bidirectional messaging becomes necessary, we'd:

1. Keep SSE for the progress feed (server → client).
2. Add a separate WebSocket endpoint for interactive commands.
3. Or — replace both with WebSockets.

Until then, SSE matches the data flow exactly.

## Interview Talking Point

> "SSE matches our data flow exactly: server pushes progress, client listens. WebSockets
> are bidirectional — solving a problem we don't have. SSE is also simpler operationally:
> no upgrade handshake, automatic reconnection, works through any HTTP infrastructure."
