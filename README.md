# Meridian

> Multi-agent due diligence system for Indian public companies (NSE / BSE).
> Produces structured, citation-backed investment memos in minutes.

Built by **Satvik Krishna**

---

## What It Does

Type a company name and ticker. Meridian spawns four specialised AI agents that gather evidence from public sources in parallel. A critic agent evaluates evidence quality. A synthesiser produces a structured memo where every claim is grounded in a cited source.

```
Financial Agent  ──┐
Market Agent     ──┼──▶  Critic Agent  ──▶  Synthesiser  ──▶  Memo
Leadership Agent ──┤
Sentiment Agent  ──┘
```

Live progress streams to the browser via Server-Sent Events — you watch each agent complete in real time.

---

## Why It Is Interesting

Most LLM applications are single-prompt wrappers. Meridian is an orchestration system with four distinct design choices worth discussing:

| Choice | Rationale |
|---|---|
| Parallel agents via `asyncio` | 4 agents run concurrently; total wall time ≈ slowest agent, not sum |
| Post-hoc critic, not inline | Batch scoring enables cross-agent analysis and independent re-runs |
| Content-addressed disk cache | SHA-256 of prompt → zero re-spend on repeated queries; reproducible evals |
| Citation-first architecture | Every finding stores source, label, value, URL — not embedded in text |

---

## Benchmark Results

Evaluated across 9 NSE-listed companies using 15 verified ground-truth claims per company.

| Company | HAL% | Citations | GT Coverage |
|---|---|---|---|
| Reliance Industries | 6% | 11 | 67% |
| TCS | 17% | 11 | 79% |
| HDFC Bank | 17% | 11 | 79% |
| Infosys | 12% | 11 | 64% |
| ITC | 11% | 11 | 86% |
| Wipro | 11% | 11 | 86% |
| ICICI Bank | 17% | 11 | 86% |
| Bharti Airtel | 22% | 11 | 79% |
| HCL Technologies | 22% | 11 | 86% |
| **Average** | **15%** | **11** | **79%** |

**HAL%** — findings flagged as unsupported by the critic agent (lower is better).  
**Citations** — unique grounded sources per run. Single-prompt baseline: 0.  
**GT Coverage** — % of verified factual claims present in the output.

Per-agent: Financial agent achieved **0% hallucination rate** across all 9 companies. People agent averaged 29%, expected given limited public data on leadership succession.

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
  │  Financial  Market  Leadership  Sent │
  │      │        │         │        │  │
  │      └────────┴─────────┴────────┘  │
  │                   │                  │
  │            Critic Agent              │
  │          (batch LLM scoring)         │
  │                   │                  │
  │            Synthesiser               │
  └───────────────────────────────────── ┘
          │
  LLM layer (Ollama local / Gemini Flash)
  + SHA-256 disk cache
```

Full design in [`docs/PLANNING.md`](docs/PLANNING.md). Architecture decisions in [`docs/decisions/`](docs/decisions/).

---

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI · Python 3.11 · asyncio |
| Frontend | Next.js 14 (App Router) · Tailwind CSS |
| Streaming | Server-Sent Events |
| LLM (dev) | Ollama `qwen2.5:7b` — local, free |
| LLM (demo) | Gemini 2.0 Flash free tier |
| Data sources | yfinance · Wikipedia API · Reddit public JSON · Google News RSS |
| Cache | Disk-based · SHA-256 content-addressed |
| Validation | Pydantic v2 |

---

## Local Setup

**Prerequisites:** Python 3.11+, Node 20+, [Ollama](https://ollama.com) running locally.

```bash
# Pull the model once
ollama pull qwen2.5:7b
```

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

**Run the evaluation benchmark:**
```bash
cd backend
python -m app.eval.benchmark
# Results saved to data/eval/report.md
```

---

## Project Structure

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
    └── decisions/       ← ADRs 001-004
```

---

## License

MIT
