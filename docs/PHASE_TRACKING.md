# Phase Tracking

> Read this at the start of every Claude Code session.
> Update at the end of every session.

---

## Current Phase

**Phase 1 — Environment Setup**

## Status

🟡 In Progress

## Last Session Summary

Phase 0 (Planning) complete. `docs/PLANNING.md` is the master plan. ADRs 001-004 documented in `docs/decisions/`. Architecture, schema, agent responsibilities, eval framework, and risk register all locked.

## Next Concrete Step

Set up local development environment:

1. Verify Python 3.11+ installed
2. Verify Node.js 20+ installed
3. Install Ollama and pull `qwen2.5:7b`
4. Initialize repo structure (backend skeleton, frontend skeleton)
5. Initialize git, commit baseline
6. Create `.env` from `.env.example`

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
- [ ] Python 3.11+ verified
- [ ] Node.js 20+ verified
- [ ] Ollama installed
- [ ] `qwen2.5:7b` pulled and tested
- [ ] Backend dir scaffolded with `pyproject.toml`
- [ ] Frontend dir scaffolded with Next.js
- [ ] Git initialized
- [ ] `.env.example` populated
- [ ] First commit pushed

### Phase 2 — Backend Skeleton
- [ ] FastAPI app with /health endpoint
- [ ] Config loading from env
- [ ] Structured logging
- [ ] SSE proof-of-concept route
- [ ] Auto-reload working

### Phase 3 — LLM Wrapper + Cache
- [ ] Ollama client wrapper
- [ ] Disk cache (content-addressed)
- [ ] Pydantic structured output validation
- [ ] Retry-once on JSON failure
- [ ] Unit tests on cache + parsing

### Phase 4 — Agent System
- [ ] Agent base class
- [ ] Financial agent end-to-end (with citations)
- [ ] Market agent
- [ ] People agent
- [ ] Customer Sentiment agent

### Phase 5 — Orchestrator
- [ ] Planner
- [ ] Async parallel runner
- [ ] Progress events

### Phase 6 — Critic Agent
- [ ] Batch scoring
- [ ] Threshold-based flagging

### Phase 7 — Synthesizer
- [ ] Memo template
- [ ] Section generation
- [ ] Citation linking

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
