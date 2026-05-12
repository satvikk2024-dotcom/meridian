# Phase Tracking

> Read this at the start of every Claude Code session.
> Update at the end of every session.

---

## Current Phase

**Phase 9.5 — Diagnostic Expansion + Surgical Fixes**

## Status

✅ Complete — M1 (ground truth + new metrics + report.py), M2 (baseline lock), M3 (HAL regression fixed), M4 (news agent)

## Last Session Summary (2026-05-10)

Completed Phase 9.5 milestones:
- **M1**: 15 ground-truth JSON files (one per benchmark company), new metrics (per-agent HAL, source breakdown, worst findings, GT coverage), `report.py` for markdown report generation, benchmark.py updated to save `report.md` + `baseline_locked.json`
- **M2**: 9-company benchmark run; baseline locked to `data/eval/baseline_locked.json`
- **M3**: HAL regression fixed — prompt changes bust LLM cache → model variance. Reverted all system prompt edits to originals. Added `skip_critic=True` for customer agent short-circuit path
- **M4**: News agent (`backend/app/sources/news.py`) — Google News RSS, no API key, returns 5 headlines as citations with `fetched_at` datetime. News NOT included in LLM prompt (preserves cache hash). Financial agent fetches news in parallel
- **News UI**: `MemoViewer.tsx` — `NewsCard` component shows headlines with publisher badge, date, external link. Renders in skeleton phase (as soon as financial agent done, ~30s before memo)
- **Critical bug fix**: `datetime` not JSON serializable — `_sse()` now uses `json.dumps(data, default=str)`
- **TypeScript**: `RawCitation` interface in `sse.ts`, `AgentState.citations: RawCitation[]`

## Next Concrete Step

**Phase 10 — Deployment**
1. Backend on Railway or Render (free tier)
2. Frontend on Vercel
3. Pre-cache demo runs for 3-4 companies so demo is instant
4. Record a 90-second demo video

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
- [x] M1: Design system foundation — tokens, Tailwind theme, Inter + JetBrains Mono fonts
- [x] M1: layout.tsx — root layout, dark background, no flash
- [x] M1: page.tsx — "MERIDIAN" placeholder in accent color
- [x] M1: runs/[id]/page.tsx — 3-column CSS grid scaffold (agents-panel, main-panel, context-rail, event-log)
- [x] M1: StatusBadge — 5 states with pulse animation
- [x] M1: SourceIcon — yfinance, wikipedia, reddit, github, news
- [x] M2: Landing page + RunForm + lib/api.ts stub
- [x] M3: Run page header + AgentsPanel + SSE hook (useRunEvents)
- [x] M4: Memo tab + CitationCard
- [x] M5: Evidence tab
- [x] M6: Trace tab + EventLog
- [x] M7: Empty/error states + polish
- [x] M8: Context rail — live stock snapshot (price, 52W range, metrics, critic score)

### Phase 9 — Evaluation Framework
- [x] 20-company benchmark dataset (22 total, 15 with benchmark:true)
- [x] Metrics: hallucination_rate, citation_count, finding_completeness
- [x] benchmark.py CLI runner (system + baseline, markdown table output)
- [x] baseline.py — single-prompt comparison (same model, no tools)
- [x] Results table added to README

### Phase 9.5 — Diagnostic Expansion + Surgical Fixes
- [x] M1: 15 ground-truth JSON files (12-15 verified claims per company)
- [x] M1: New metrics — per_agent_hallucination, source_citation_breakdown, worst_findings, ground_truth_coverage
- [x] M1: report.py — markdown report with baseline comparison table
- [x] M1: benchmark.py updated — saves report.md + baseline_locked.json
- [x] M2: 9-company benchmark baseline locked
- [x] M3: HAL regression fixed — reverted prompt changes, added skip_critic flag for customer agent
- [x] M4: news.py source — Google News RSS, no API key, datetime-stamped headlines
- [x] M4: Financial agent fetches news in parallel (not in LLM prompt — cache-safe)
- [x] M4: NewsCard UI in MemoViewer — renders during skeleton phase, not just after memo
- [x] Bug: datetime serialization in _sse() — json.dumps(..., default=str)

### Phase 10 — Deployment
- [ ] Backend on Railway/Render
- [ ] Frontend on Vercel
- [ ] Pre-cached demo runs
- [ ] Demo video recorded

### Phase 11 — Resume + Interview Prep
- [x] Resume bullet finalized (with real benchmark numbers)
- [x] 3 interview stories written (critic architecture, cache-busting failure, product insight)
- [x] README polished — real numbers, clean structure, no filler
- [x] FUTURE.md cleaned up

---

## Open Blockers

_None yet._

## Recent Decisions

See `docs/decisions/` for ADRs.

## Recently Parked Ideas

See `FUTURE.md`.
