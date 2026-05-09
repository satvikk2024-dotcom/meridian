# Phase Tracking

> Read this at the start of every Claude Code session.
> Update at the end of every session.

---

## Current Phase

**Phase 4 — Agent System**

## Status

✅ Complete — all 4 agents + base class + sources

## Last Session Summary

Phase 0 (Planning) complete. `docs/PLANNING.md` is the master plan. ADRs 001-004 documented in `docs/decisions/`. Architecture, schema, agent responsibilities, eval framework, and risk register all locked.

Prerequisites verified and installed (2026-05-08):
- Python 3.11.9 installed via pyenv, pinned to project via `.python-version`
- Node.js 20.20.2 installed via Homebrew, added to PATH in `.zshrc`
- Ollama 0.23.1 installed and running as background service
- `qwen2.5:7b` (4.7GB) pulled and smoke-tested

Git repo initialized, initial commit on `main` branch.

## Next Concrete Step

Phase 8 — Frontend (Next.js):
1. `frontend/app/page.tsx` — run form (company name + ticker input)
2. `frontend/components/ProgressFeed.tsx` — SSE consumer showing live agent progress
3. `frontend/components/MemoViewer.tsx` — renders the markdown memo with citation links
4. `frontend/lib/api.ts` — EventSource wrapper for the SSE stream

## Phase Checklist

### Phase 0 — Planning
- [x] Problem statement scoped
- [x] Architecture diagram
- [x] Folder structure designed
- [x] Database schema drafted
- [x] Agent responsibilities defined
- [x] Eval framework designed
- [x] Caching strategy defined
- [x] 14-day roadmap
- [x] Risk register
- [x] ADRs 001-004 written

### Phase 1 — Environment Setup (current)
- [x] Python 3.11+ verified (3.11.9 via pyenv)
- [x] Node.js 20+ verified (20.20.2 via Homebrew)
- [x] Ollama installed (0.23.1)
- [x] `qwen2.5:7b` pulled and tested
- [x] Git initialized
- [x] `.env.example` populated
- [x] First commit pushed
- [x] Backend dir scaffolded with `pyproject.toml`
- [x] Frontend dir scaffolded with Next.js
- [x] `.env` created from `.env.example`

### Phase 2 — Backend Skeleton
- [x] FastAPI app with /health endpoint
- [x] Config loading from env (pydantic-settings)
- [x] Structured logging (structlog)
- [x] SSE proof-of-concept route (streams 14 fake events end-to-end)
- [x] Auto-reload working (uvicorn --reload)

### Phase 3 — LLM Wrapper + Cache
- [x] Ollama client wrapper (app/llm/client.py)
- [x] Disk cache content-addressed by SHA-256 (app/llm/cache.py)
- [x] Pydantic structured output validation (app/llm/schemas.py)
- [x] Retry-once on JSON failure with schema in corrective prompt
- [x] 9 unit tests — 9 passed (cache + parse/retry logic)
- [x] Live smoke test: Reliance Industries — 6s first call, 0.000s cached

### Phase 4 — Agent System
- [x] Agent base class (AgentResult, Citation, Agent ABC)
- [x] Financial agent end-to-end (yfinance + Wikipedia + LLM findings + citations)
- [x] Market agent (price momentum, valuation, sector position)
- [x] People agent (yfinance officers + Wikipedia context)
- [x] Customer Sentiment agent (Reddit r/IndiaInvestments + r/IndianStockMarket)

### Phase 5 — Orchestrator
- [x] Planner (agents_for — returns all 4 agents, extensible)
- [x] Async parallel runner (asyncio.Queue fan-out, SSE event generator)
- [x] Progress events (run_started, agent_started×4, agent_done×4, run_complete)
- [x] GET /api/runs/stream wired into FastAPI, verified over HTTP

### Phase 6 — Critic Agent
- [x] AgentCriticOutput: flat-list schema (supported/partially_supported/unsupported)
- [x] Batch scoring: 4 critic LLM calls in parallel (one per agent)
- [x] Hallucination rate computed across all findings
- [x] critic_done SSE event emitted after agents, before run_complete
- [x] Verified: 33% hallucination rate on Reliance run (correctly flags confidence fields)

### Phase 7 — Synthesizer
- [x] templates.py: Section definitions + FIELD_LABELS mapping
- [x] memo.py: build_memo() assembles full markdown from AgentResults + CriticResult
- [x] Critic flags rendered inline next to flagged findings
- [x] Risk Summary aggregates risks across all agents
- [x] Citations section with deduplicated, linked sources
- [x] memo field added to run_complete SSE event

### Phase 8 — Frontend
- [ ] Run form
- [ ] Live progress feed (SSE consumer)
- [ ] Memo viewer
- [ ] Citation hover cards

### Phase 9 — Evaluation Framework
- [ ] 20-company benchmark dataset
- [ ] Metrics: accuracy, citation precision, hallucination rate
- [ ] Baseline single-prompt comparison
- [ ] Results table for README

### Phase 10 — Deployment
- [ ] Backend on Railway/Render
- [ ] Frontend on Vercel
- [ ] Pre-cached demo runs
- [ ] Demo video recorded

### Phase 11 — Resume + Interview Prep
- [ ] Resume bullet finalized
- [ ] LinkedIn post drafted
- [ ] README polished
- [ ] 3 interview stories rehearsed

---

## Open Blockers

_None yet._

## Recent Decisions

See `docs/decisions/` for ADRs.

## Recently Parked Ideas

See `FUTURE.md`.
