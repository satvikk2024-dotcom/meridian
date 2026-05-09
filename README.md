# Meridian

> Multi-agent due diligence system for Indian public companies. Produces structured, citation-backed investment memos in under 60 seconds.

---

## What It Does

Type a company name. Meridian spawns four specialized AI agents — Financial, Market, Leadership, and Customer Sentiment — that gather evidence from public sources in parallel. A critic agent evaluates evidence quality, then a synthesizer produces a structured memo where every claim is cited.

## Why It's Interesting

Most LLM products are single-prompt wrappers. Meridian is an orchestration system:

- **Multi-agent parallel execution** via `asyncio` — 4 agents run concurrently, not sequentially
- **Citation grounding** — every finding links to a specific yfinance, Wikipedia, or Reddit source
- **Adversarial critic agent** — scores each finding as `supported / partially_supported / unsupported` before synthesis
- **Streaming UI** — live agent progress via Server-Sent Events, no polling
- **Evaluation framework** — benchmarked against a single-prompt baseline across 6 companies

## Benchmark Results

Evaluated across 6 Indian public companies (Reliance Industries, TCS, HDFC Bank, Infosys, Zomato, Wipro).

| Company | HAL% | Citations | Completeness |
|---------|------|-----------|--------------|
| Reliance Industries | 23% | 16 | 96% |
| TCS | 27% | 16 | 96% |
| HDFC Bank | 20% | 16 | 100% |
| Infosys | 8% | 16 | 100% |
| Zomato | 62% | 15 | 96% |
| Wipro | 26% | 16 | 100% |
| **Average** | **28%** | **15.8** | **98%** |

**HAL%** = findings flagged as weakly evidenced by the critic agent.
**Citations** = unique grounded sources per run. Baseline (single-prompt, no tools) = 0.
**Completeness** = % of expected fields populated across all 4 agents.

## Architecture

```
User → Next.js frontend → FastAPI SSE stream
                              ↓
                    Orchestrator (asyncio)
                    ├── Financial Agent  (yfinance + Wikipedia)
                    ├── Market Agent     (yfinance)
                    ├── Leadership Agent (yfinance + Wikipedia)
                    └── Sentiment Agent  (Reddit public API)
                              ↓
                    Critic Agent (parallel batch scoring)
                              ↓
                    Synthesizer → Markdown memo
```

Full design in `docs/PLANNING.md`. Architecture decisions in `docs/decisions/`.

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI + Python 3.11 + asyncio |
| Frontend | Next.js 14 (App Router) + Tailwind |
| Streaming | Server-Sent Events |
| LLM (dev) | Ollama `qwen2.5:7b` (local, free) |
| Data | yfinance, Wikipedia API, Reddit public JSON |
| Cache | Disk-based, SHA-256 content-addressed |
| Validation | Pydantic v2 |

## Local Development

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

**Requires:** Ollama running locally with `qwen2.5:7b` pulled.

**Run benchmark:**
```bash
cd backend
python -m app.eval.benchmark
```

## Status

| Phase | Status |
|---|---|
| 0 — Planning | ✅ Complete |
| 1 — Environment Setup | ✅ Complete |
| 2 — Backend Skeleton | ✅ Complete |
| 3 — LLM Wrapper + Cache | ✅ Complete |
| 4 — Agent System | ✅ Complete |
| 5 — Orchestrator | ✅ Complete |
| 6 — Critic Agent | ✅ Complete |
| 7 — Synthesizer | ✅ Complete |
| 8 — Frontend | ✅ Complete |
| 9 — Evaluation | ✅ Complete |
| 10 — Deployment | ⏳ |
| 11 — Resume + Interview Prep | ⏳ |

## License

MIT
