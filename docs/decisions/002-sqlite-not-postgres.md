# ADR-002: Use SQLite (not Postgres) for the MVP

## Status
Accepted — 2026-05

## Context

Meridian needs a transactional store for runs, evidence, findings, citations, memos,
and an LLM cache. Options:

- **SQLite** — In-process file-based DB. No server.
- **Postgres** — Full-featured RDBMS. Server-based.
- **DuckDB** — Analytical embedded DB. Great for OLAP, not for transactional writes.

## Decision

SQLite for the MVP, accessed via SQLModel (which sits on SQLAlchemy + Pydantic).

## Reasoning

- The MVP runs as a single process. SQLite's "one writer at a time" limitation is irrelevant.
- SQLite is a single file — trivial to back up, share, delete, reset.
- No server, no auth, no connection pooling — less operational overhead during dev.
- SQLModel keeps the data layer portable; swapping to Postgres is a connection-string change.

## Consequences

**Positive:**
- Zero setup overhead.
- Faster iteration during dev (no docker compose, no service to start).
- Demos run anywhere a Python process can.

**Negative:**
- Concurrent writes will block each other (acceptable; we don't have concurrent writers).
- Some Postgres-specific features (JSONB indexes, full-text search) aren't available.

## Migration Path

When we need Postgres (multi-user deploy, concurrent writers, hosted environments that wipe disk):

1. Update `DATABASE_URL` in `.env`.
2. Add `asyncpg` to dependencies.
3. Replace any SQLite-specific syntax (rare with SQLModel).
4. Run schema migration with Alembic (which we'll add at that point — not yet).

Estimated migration effort: under an hour.

## Interview Talking Point

> "I chose SQLite because the bottleneck for an MVP is iteration speed, not database performance.
> Because I used SQLModel, swapping to Postgres later is a connection-string change plus one
> dependency. I'd add migrations only when more than one person is writing to the DB."
