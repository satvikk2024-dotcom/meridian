# Meridian

Multi-agent due diligence system for NSE/BSE companies — cited memos in ~75s, evaluated against 135 verified ground-truth claims.

Built by **Satvik Krishna**

---

## Evaluation

Benchmarked across 9 NSE-listed companies, 15 verified ground-truth claims per company (135 total). Baseline: single-prompt LLM given the same inputs, no agents, no critic.

| Metric | Meridian | Single-prompt baseline |
|---|---|---|
| Avg hallucination rate | 15% | not measured |
| Ground-truth coverage | 79% | not measured |
| Unique citations per run | 11 | 0 |
| Financial agent hallucination | **0%** (all 9 cos.) | — |

Per-agent hallucination varies with how much public data exists to ground against: financial (0%, hard numbers from yfinance) < market (20%) < people (29%, leadership/succession is thin on public sources). Full per-company breakdown and methodology: [`data/eval/report.md`](data/eval/report.md).

---

## What it does

Generating investment memos with an LLM is easy. Generating ones you can trust is not — the default failure mode is confident, well-written hallucination with no way to trace which claim came from where.

Meridian addresses this by keeping evidence and claims as separate, structured objects instead of letting the model free-write a memo from a blob of context. Four agents (financial, market, people, customer sentiment) each fetch their own evidence in parallel and produce findings tied to that evidence. A separate critic pass then checks every finding against the evidence the agent that produced it actually had — not against ground truth, but against faithfulness: did this claim come from something retrieved, or did the model add it? Findings that fail are flagged inline in the final memo rather than silently shipped.

This moves the trust problem from "did the LLM sound confident" to "can I see the source for this specific line" — and it's checkable by anyone who clones the repo and reruns the benchmark.

```
Financial Agent  ──┐
Market Agent     ──┼──▶  Critic Agent  ──▶  Synthesizer  ──▶  Memo
People Agent     ──┤
Sentiment Agent  ──┘
```

Progress streams to the browser live via Server-Sent Events as each agent completes.

---

## Architecture

```
Browser
  │
  ├── POST /api/runs          ← start a run
  └── GET  /api/runs/stream   ← SSE event stream
          │
          ▼
  FastAPI + asyncio
          │
  ┌───────┴──────────────────────────────┐
  │           Orchestrator               │
  │    asyncio.Queue fan-out / fan-in    │
  │                                      │
  │  Financial  Market  People  Sentiment│
  │      │        │       │        │    │
  │      └────────┴───────┴────────┘    │
  │                   │                  │
  │            Critic Agent              │
  │          (batch LLM scoring)         │
  │                   │                  │
  │            Synthesizer               │
  └───────────────────────────────────── ┘
          │
  LLM layer (Ollama qwen2.5:7b, local)
  + SHA-256 content-addressed disk cache
```

The orchestrator starts all 4 agents concurrently and bridges their async tasks to a single SSE stream via an `asyncio.Queue` — each agent pushes progress events the moment it finishes, so total wall time tracks the slowest agent, not the sum. The critic and synthesizer only run after every agent has returned, since grounding checks need each agent's full evidence set to exist first.

**Key decisions:**
- [ADR-001: Async agents over Celery/task queue](docs/decisions/001-async-not-celery.md)
- [ADR-002: SQLite over Postgres for MVP](docs/decisions/002-sqlite-not-postgres.md)
- [ADR-003: SSE over WebSockets](docs/decisions/003-sse-not-websockets.md)
- [ADR-004: Local Ollama over paid API](docs/decisions/004-local-ollama-no-paid-api.md)
- [ADR-005: Indian market (NSE/BSE) over US](docs/decisions/005-indian-market-not-us.md)

---

## Setup

**Prerequisites:** Python 3.11+, Node 20+, [Ollama](https://ollama.com) running locally.

```bash
ollama pull qwen2.5:7b

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install && npm run dev   # http://localhost:3000

# Reproduce the benchmark
cd backend
python -m app.eval.benchmark   # writes data/eval/report.md
```

---

## What this doesn't do

- NSE/BSE only — no international markets, no multi-exchange support
- No real-time data — yfinance quotes are delayed, not streamed
- Local Ollama (qwen2.5:7b) sets the quality ceiling; a larger hosted model would likely lower the hallucination rate but costs money
- The 135-claim ground-truth set was manually curated by one person, not independently verified by a third party
- Customer sentiment agent is Reddit-only (r/IndiaInvestments, r/IndianStockMarket) — thin coverage for less-discussed companies

---

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI · Python 3.11 · asyncio |
| Frontend | Next.js 14 (App Router) · Tailwind CSS |
| Streaming | Server-Sent Events |
| LLM | Ollama `qwen2.5:7b` (local) |
| Cache | SHA-256 content-addressed disk cache |
| Data sources | yfinance · Wikipedia API · Reddit public JSON · Google News RSS |
| Validation | Pydantic v2 |

---

## Project structure

```
meridian/
├── backend/app/
│   ├── agents/          ← financial, market, people, customer, critic
│   ├── orchestrator/    ← planner + async runner
│   ├── synthesizer/     ← memo builder + templates
│   ├── sources/         ← yfinance, wikipedia, reddit, news fetchers
│   ├── llm/             ← client, SHA-256 cache, Pydantic schemas
│   └── eval/            ← benchmark runner, metrics, ground-truth dataset
├── frontend/
│   ├── app/             ← Next.js App Router pages
│   ├── components/      ← MemoViewer, AgentsPanel, ContextRail, ...
│   └── lib/             ← SSE hook, API helpers
└── docs/
    ├── PLANNING.md      ← master architecture document
    ├── PHASE_TRACKING.md
    └── decisions/       ← ADRs 001-005
```

---

## License

MIT
