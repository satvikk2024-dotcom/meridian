# ADR-001: Use asyncio (not Celery / Redis / Temporal) for parallel agent execution

## Status
Accepted — 2026-05

## Context

Meridian needs to run 4 research agents in parallel and stream progress to the client.
Several patterns can deliver parallelism:

- **asyncio** — Python's built-in concurrency primitive. Single-process, single event loop.
- **Celery + Redis** — Distributed task queue. Workers pull jobs from a Redis broker.
- **Temporal** — Durable workflow orchestration. Survives restarts, handles retries declaratively.
- **AWS Step Functions / Cloud-native equivalents** — Managed orchestration.

## Decision

Use `asyncio` + `asyncio.gather` inside a single FastAPI process.

## Reasoning

- The MVP target is a few concurrent runs at most. asyncio handles this trivially.
- Celery introduces a Redis dependency, a worker process, a result backend, and serialization concerns.
  All for a problem we don't yet have.
- Temporal is excellent but is a workflow framework, not a library. Adopting it for a 2-week MVP is overkill.
- Recruiters at the kind of companies we're targeting (AI startups, technical PM roles) value
  appropriate complexity, not maximum complexity. Choosing asyncio shows judgment.

## Consequences

**Positive:**
- One process, one runtime, easy to reason about.
- Zero infrastructure beyond a Python process.
- Faster development.
- Easier debugging — no message queue to inspect.

**Negative:**
- Doesn't scale beyond ~50 concurrent runs in a single process.
- Long-running runs are tied to the process lifetime; a restart loses in-flight work.
- No built-in retry/durability story; we add this in code.

## Migration Path

If we ever need to scale or harden, the swap path is:

- Move agent invocation behind a `JobQueue` abstraction.
- Implement the abstraction first as `InProcessQueue` (asyncio); later as `CeleryQueue`.
- Persistence already lives in SQLite/Postgres, so durability is partially solved already.

## Interview Talking Point

> "I picked asyncio because the bottleneck wasn't concurrency — it was clarity. Celery would have
> added a broker, a worker, and a serialization layer to solve a problem I didn't have. If usage
> grew, I have a clean migration path because agent invocation goes through a queue abstraction."
