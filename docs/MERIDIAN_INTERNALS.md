# MERIDIAN INTERNALS
## Complete Technical Reference

---

# Part 0 — How To Use This Document

This document is organized from high-level to low-level, then pivots to cross-cutting concerns, then ends with interview preparation material.

**First read (30 min):** Part 1 (three-level explanation), Part 2 (problem and insight), Part 3 (system architecture). These give you the mental model. Everything else is reference.

**Before an interview:** Part 17 (trade-offs), Part 19 (interview Q&A), Part 21 (cheat sheet). Read these the night before. The cheat sheet fits on one page — print it.

**When debugging something specific:** Part 15 (failure encyclopedia) is indexed by failure mode. Part 4 (component deep dives) is indexed by file path.

**When explaining the system to someone:** Part 5 (multi-agent pattern), Part 6 (retrieval and citation), Part 7 (async and streaming). These are the "this is how it actually works" sections.

**Reference during development:** Part 4 (every component), Part 14 (every API endpoint), Part 9 (data sources), Part 10 (models).

**Understanding the gaps:** Part 12 (database: planned vs. reality) and the divergence callouts scattered through Part 4 are the honest accounting of what was planned but not built.

The glossary (Part 20) defines every term used in the project. If a concept appears and you're not sure what it means in this specific context, check there first.

---

# Part 1 — Meridian At Three Levels Of Depth
self-evaluation bias" or "in-context confirmation bias.
over evaluation
I have a critic agent that scores findings for hallucination — but it's important to be precise about what it actually does. It checks whether claims accurately summarize their cited evidence. It does NOT verify against the real world, and it doesn't cross-check across sources. There's a well-known limitation here: when both the agent and the critic see the same evidence, they tend to agree, because the claim was constructed from that evidence in the first place. So the critic mostly catches over-elaboration and obvious LLM errors. Real verification would require either cross-source corroboration or cross-agent contradiction detection — both of which I have as v2 work in my future doc. For v1, an imperfect confidence signal was better than no signal, and the architecture supports adding stronger verification layers without redesigning the pipeline.v

## 30-Second Version

Meridian is a multi-agent research system that produces structured investment memos for Indian public companies. You give it a company name and ticker; four specialized AI agents run in parallel to gather financial data, market position, leadership, and customer sentiment; a critic scores every claim for hallucination; a synthesizer assembles the findings into a markdown memo with inline citations. The interesting part is not the AI — it is the orchestration: fan-out concurrency, post-hoc verification, structured output validation, and an evaluation framework that benchmarks the system against a 15-claim ground-truth dataset for 15 companies.

## 5-Minute Version

**The agents.** Four agents run concurrently: Financial (revenue, margins, debt ratios from yfinance + Wikipedia + Google News RSS), Market (competitive position, sector data from yfinance), People (leadership, officers from yfinance + Wikipedia), and Customer Sentiment (Reddit mentions, public JSON API, no auth). Each agent fetches its own data sources, builds a structured prompt, calls the LLM, and returns a typed `AgentResult` with findings (key-value pairs), citations (source, URL, label, timestamp), and a confidence score. All of this is Pydantic-validated — the LLM must return parseable JSON or the system retries once with a concrete example injected into the prompt.

**The critic.** After agents complete, a separate critic pass scores each finding for hallucination likelihood. It runs eligible findings in parallel (skipping Customer agent findings when there were too few Reddit posts). The critic returns a score per finding and an overall `hallucination_rate`. This is a post-hoc verification step — it does not change the findings, it annotates them. The annotated results flow into the memo.

**The synthesizer.** `build_memo()` assembles a markdown document from all agent results and critic scores. It deduplicates citations, structures findings under section headers, and adds a critic summary block. The memo is plain markdown — no custom format, deliberately. The frontend parses it back into structured UI components.

**Streaming.** Everything is delivered via Server-Sent Events. The orchestrator's `run_all()` is an async generator. Each `agent_started`, `agent_done`, and `critic_done` event is JSON-serialized and sent as an SSE frame. The frontend holds all state in a `useReducer` hook driven by these events. When the final `memo_ready` event arrives, the memo markdown is in the payload and the UI renders it immediately.

**Evaluation.** A benchmark runner loads a dataset of 15 Indian companies, each with 15 hand-written ground-truth claims, runs the full system, and computes hallucination rate, citation count, finding completeness, and ground-truth coverage. A baseline (single LLM call, no tools, no agents) runs on the same dataset for comparison. Results are written to `data/eval/report.md` and `data/eval/results.json`.

## 30-Minute Version

**Entry point and config.** `backend/app/main.py` creates the FastAPI application, registers CORS middleware (open in dev), and mounts the router from `api/runs.py`. There is a lifespan hook but it does nothing substantive — the store module was planned to initialize the database here, but the store was never built. The only active route besides `/health` is `GET /api/runs/stream`.

**Configuration.** `config.py` uses pydantic-settings to load environment variables from `.env`. Fields include `ollama_base_url`, `ollama_model`, `gemini_api_key`, `anthropic_api_key`, `database_url`, `synthesizer_provider`, and `cache_dir`. Most of these are loaded but not used — the Gemini and Anthropic keys are never routed to, the database URL is never connected, and `synthesizer_provider` is never read by `memo.py`. The active fields are `ollama_base_url`, `ollama_model`, and `cache_dir`.

**LLM layer.** `llm/client.py` exposes a single `complete()` async function. It computes a SHA-256 cache key from the model name, system prompt, user prompt, and json_mode flag. It checks `data/cache/llm/` for a matching file. On cache hit, it returns immediately — no network call. On miss, it POSTs to the Ollama HTTP API and writes the response to disk. `llm/schemas.py` defines `LLMOutputBase` (the base Pydantic class all agent schemas inherit from) and `parse_response()`, which tries `model_validate_json` first, then on failure builds a concrete example from the schema and retries once. This single retry mechanism cut parse failures from ~12% to ~1%.

**Agents.** Each agent is a subclass of the abstract `Agent` base class from `agents/base.py`. The base class defines `run(ticker, company_name)` as the required method. Each agent implements this by: (1) fetching data from its assigned sources, (2) building a text prompt from that data, (3) calling `complete()`, (4) calling `parse_response()`, (5) returning an `AgentResult`. `AgentResult` holds findings (a list of `Finding` objects, each with label, value, and optional flag), citations (a list of `Citation` objects), confidence (0.0–1.0), and `skip_critic` (bool). The `Citation` dataclass carries source name, URL, display label, a snippet of the cited content, and `fetched_at` timestamp.

**Orchestrator.** `orchestrator/planner.py` decides which agents to run. Currently `agents_for()` returns all four agents always — no per-company customization. `orchestrator/runner.py` contains `run_all()`, an async generator that creates an `asyncio.Queue`, launches all four agents as concurrent tasks, puts lifecycle events into the queue as each agent starts and finishes, yields events from the queue in order, then `await asyncio.gather(*tasks)` to collect results. After all agents finish, it runs the critic and yields `critic_done`, then runs the synthesizer and yields `memo_ready`. The generator approach means the FastAPI SSE endpoint can simply iterate over `run_all()` and write each event as a frame.

**Data sources.** `sources/bse.py` wraps yfinance — despite the name, it calls Yahoo Finance with `.NS` (NSE) or `.BO` (BSE) ticker suffixes, not BSE's official API. `sources/wikipedia.py` wraps the `wikipediaapi` library. `sources/reddit.py` hits Reddit's public JSON API (`/r/{subreddit}/search.json`) with no authentication. `sources/news.py` hits Google News RSS and parses XML. Each fetcher runs in a thread executor (`asyncio.get_event_loop().run_in_executor`) because these are blocking I/O calls.

**Critic.** `agents/critic.py` defines `CriticResult` and `run_critic()`. It receives all `AgentResult` objects, filters out those with `skip_critic=True`, and scores eligible findings in parallel. The `_EXCLUDED_FROM_CRITIC` set (`{"confidence", "error"}`) removes meta-fields before scoring. The critic calls the LLM once per eligible result, asking it to score each finding on a 0–1 hallucination likelihood scale. Results are aggregated into an overall rate.

**Synthesizer.** `synthesizer/memo.py` takes all `AgentResult` objects and the `CriticResult` and assembles a markdown string. It iterates through `synthesizer/templates.py`'s `SECTIONS` list to maintain consistent section order. Citations are deduplicated using a `seen: set[str]` keyed on `f"{c.source}:{c.label}"`. The output is pure markdown — no JSON, no custom format.

**Frontend.** The Next.js 14 app uses the App Router. The run page (`app/runs/[id]/page.tsx`) is a server component that extracts company and ticker from URL search params and passes them to `RunPageClient.tsx`, which is the interactive client component. `RunPageClient` uses the `useRunEvents` hook from `lib/sse.ts`, which manages an `EventSource` connection and feeds events through a `useReducer` to build `RunState` (containing `AgentState` for each agent, the memo markdown, critic scores, and all citations). The CSS grid in `RunPageClient` divides the screen into six named areas across three columns and three rows.

**Evaluation.** `eval/benchmark.py` loads JSON files from `eval/dataset/` (one per company, with ticker, company name, and 15 ground-truth claims), runs the full Meridian pipeline on each, collects `AgentResult` objects, and passes them to `eval/metrics.py`. Metrics include hallucination rate (from critic), citation count, finding completeness (required fields present), and ground-truth coverage (keyword matching of claims against findings). `eval/report.py` formats results into markdown. `eval/baseline.py` runs a single LLM call with no tools on the same dataset for comparison.

---

# Part 2 — The Problem And The Insight

## The Real-World Workflow This Replaces

A buy-side analyst covering an Indian mid-cap might spend two to four hours per company doing initial due diligence: pulling the latest quarterly results from BSE/NSE filings, checking Wikipedia for company history, reading analyst notes and news for the past quarter, scanning Reddit and financial Twitter for retail sentiment, and synthesizing all of it into a structured memo before presenting to the investment committee. The memo covers financials, competitive position, management quality, and sentiment — exactly the four domains Meridian's agents cover.

The time cost is real. The bottleneck is not intelligence — it is information gathering and structuring. A trained analyst spends more time reformatting tables from PDFs and copy-pasting numbers into Excel than thinking about whether the numbers are good. Meridian automates the first pass: gather, structure, cite, flag uncertainty. The human does the second pass: judgment, context, decision.

## Why Single-Prompt LLMs Fail At This

A naive approach — "you are a financial analyst, write a due diligence memo on Reliance Industries" — fails for three reasons:

**Hallucination without grounding.** An LLM has training-time knowledge of Reliance, but that knowledge is stale, incomplete, and unverifiable. It will confidently state revenue figures that may be off by a year, a currency, or fabricated entirely. There is no mechanism to distinguish true claims from plausible-sounding ones.

**No citations.** A memo with no citations is not useful for a professional workflow. Every claim must be traceable to a source. A single-prompt LLM cannot produce citations because it has no retrieval step — it has no sources to cite.

**Context limits and coherence.** Fitting comprehensive financial data for one company into a single prompt is feasible, but across 15 companies in an eval run it becomes expensive and brittle. Specialized agents each handle a smaller, well-scoped prompt with specific data attached.

## The Core Insight: Parallel Specialized Agents Plus Post-Hoc Critic

The architectural insight is to separate three things that single-prompt LLMs conflate: retrieval, generation, and verification.

Retrieval happens in the data source fetchers — no LLM involved. Generation happens in each agent — LLM with structured data attached and schema-constrained output. Verification happens in the critic — a separate LLM pass that sees findings and asks whether they are plausible given the evidence, without the generative pressure to produce a complete memo.

The critic is post-hoc by design. An inline critic (having the same LLM generation evaluate its own output) is known to be weaker than a separate pass. The critic here is a distinct call with a distinct prompt, seeing only the findings (not the generation prompt), which reduces the risk of the critic simply agreeing with whatever was generated.

## What Meridian Is NOT Trying To Do

Meridian does not replace analyst judgment. It does not make buy/sell recommendations. It does not have access to real-time data (yfinance has a delay; news RSS has a delay). It does not handle options, futures, or derivatives data. It does not produce SEBI-compliant research reports. It is not a production system — it has no authentication, no database, no rate limiting, and no persistence between runs. It is a demonstration of orchestration patterns, structured LLM output, and evaluation methodology.

---

# Part 3 — Top-Down System Architecture

## ASCII Diagram

```
Browser
  │
  │  HTTP GET /api/runs/stream?company=...&ticker=...
  ▼
FastAPI (backend/app/main.py)
  │
  ├── api/runs.py  ──  StreamingResponse (SSE)
  │       │
  │       ▼
  │   orchestrator/runner.py  ──  run_all() async generator
  │       │
  │       ├── orchestrator/planner.py  ──  agents_for()
  │       │       └── returns [Financial, Market, People, Customer]
  │       │
  │       ├── asyncio.Queue  ──  fan-out lifecycle events
  │       │
  │       ├── agents/financial.py  ─────┐
  │       ├── agents/market.py     ─────┤  concurrent via asyncio.gather
  │       ├── agents/people.py     ─────┤
  │       └── agents/customer.py   ─────┘
  │               │
  │               │  each agent:
  │               ├── sources/bse.py       (yfinance, thread executor)
  │               ├── sources/wikipedia.py (wikipediaapi, thread executor)
  │               ├── sources/reddit.py    (Reddit JSON API, aiohttp)
  │               ├── sources/news.py      (Google News RSS, aiohttp)
  │               │
  │               ├── llm/client.py
  │               │       ├── llm/cache.py  ──  SHA-256 disk cache
  │               │       │       └── data/cache/llm/{hash}.json
  │               │       └── Ollama HTTP API (localhost:11434)
  │               │
  │               └── llm/schemas.py  ──  parse_response() + retry
  │
  │       after agents complete:
  │       ├── agents/critic.py  ──  run_critic()  (parallel per-result)
  │       └── synthesizer/memo.py  ──  build_memo()
  │               └── synthesizer/templates.py
  │
  └── SSE frames → Browser EventSource
          │
          ▼
      frontend/lib/sse.ts  ──  useRunEvents hook
          │
          ├── useReducer  ──  RunState
          │
          └── React components
                  ├── AgentsPanel.tsx
                  ├── MemoViewer.tsx  ──  lib/memo.ts (parseMemo)
                  ├── EvidenceTab.tsx
                  ├── TraceTab.tsx
                  ├── ContextRail.tsx
                  └── EventLog.tsx
```

## Data Flow Trace: "User clicks Reliance Industries"

1. User selects "Reliance Industries" chip on the landing page (`app/page.tsx`). `RunForm.tsx` populates company="Reliance Industries" and ticker="RELIANCE".

2. User clicks Run. `RunForm.tsx` calls `buildStreamUrl()` from `lib/api.ts`, which constructs `/api/runs/stream?company=Reliance+Industries&ticker=RELIANCE`. The browser navigates to `app/runs/[id]/page.tsx` where id is a slug like `reliance-industries-1715430000`.

3. `RunPageClient.tsx` mounts. `useRunEvents(url)` from `lib/sse.ts` opens an `EventSource` to the constructed URL.

4. `api/runs.py` receives the GET request. It creates an `asyncio.Queue` (indirectly, via `run_all()`), and returns a `StreamingResponse` that iterates over `run_all("Reliance Industries", "RELIANCE")`.

5. `runner.py`'s `run_all()` calls `planner.agents_for()` which returns all four agent instances.

6. Four `asyncio.create_task()` calls launch the agents concurrently. Each task puts `agent_started` into the queue immediately. `run_all()` yields `agent_started` events for all four — the frontend's `AgentsPanel` shows all four agents as "running" with live timers.

7. Each agent runs in parallel:
   - `financial.py` calls `fetch_stock_data("RELIANCE.NS")` (yfinance, thread executor), `fetch_summary("Reliance Industries")` (Wikipedia, thread executor), and `fetch_news("Reliance Industries")` (Google News RSS, aiohttp) — all three via `asyncio.gather`.
   - `market.py` calls `fetch_stock_data("RELIANCE.NS")` alone.
   - `people.py` calls `yf.Ticker("RELIANCE").info` directly (note: separate call from financial agent) and `fetch_summary("Reliance Industries")`.
   - `customer.py` calls `fetch_mentions("reliance industries", subreddits=["IndiaInvestments", ...])`.

8. Each agent builds a prompt from its fetched data, calls `llm/client.py`'s `complete()`, which checks `data/cache/llm/` for a matching SHA-256 hash. On cache miss, it POSTs to Ollama at `localhost:11434`.

9. Ollama returns JSON. `parse_response()` calls `model_validate_json()`. If it fails (malformed JSON from LLM), it builds a concrete example schema and retries once.

10. Each agent returns an `AgentResult`. The task puts `agent_done` into the queue. `run_all()` yields these events. The frontend marks each agent complete and shows its findings count.

11. After all four tasks complete (tracked by `for _ in range(len(agents) * 2): yield await queue.get()`), `run_all()` calls `run_critic()` with all results.

12. The critic filters out Customer agent results (likely `skip_critic=True` if fewer than 3 relevant Reddit posts). It scores Financial, Market, and People findings in parallel. Returns `CriticResult`. `run_all()` yields `critic_done`.

13. `build_memo()` assembles the markdown string. Citations are deduplicated. Sections appear in `SECTIONS` order. `run_all()` yields `memo_ready` with the full markdown in the payload.

14. The `StreamingResponse` ends. The `EventSource` in the browser receives the final event and the connection closes.

15. The `useRunEvents` reducer processes `memo_ready`: it stores the markdown string in `RunState.memo`. `MemoViewer.tsx` receives the markdown prop, calls `parseMemo()` from `lib/memo.ts`, which splits on `^## ` boundaries, extracts `**Label**` field headers and their values, parses the Citations section with a regex, and returns a `ParsedMemo` object. `MemoViewer` renders `SectionCard` components for each section, with flagged fields highlighted and citations linked.

---

# Part 4 — Bottom-Up Component Deep Dives

### main.py
**Location:** `backend/app/main.py`
**Purpose:** FastAPI application entry point, CORS configuration, route registration, and lifespan hook.
**Why it exists:** Every FastAPI app needs an application object. This is where middleware, routers, and startup/shutdown hooks attach.
**Inputs:** None at import time; receives HTTP requests at runtime.
**Outputs:** ASGI application object consumed by uvicorn.
**Key functions/classes:**
- `app = FastAPI(lifespan=lifespan)` — the application object with a lifespan context manager.
- `lifespan()` — async context manager; runs startup logic before `yield`, shutdown logic after. Currently contains no active logic (the database init that was planned for here was never built).
- `CORSMiddleware` — open (`allow_origins=["*"]`) in dev. Required because the Next.js frontend runs on port 3000 and the FastAPI backend runs on port 8000.
- `/health` route — returns `{"status": "ok"}`. Used by the frontend to check backend availability.

**The non-obvious choice:** The lifespan hook is wired but empty. This is not an oversight — it is a placeholder. The store module was planned to create the SQLite database and run table migrations here. When store/ is built, one import and one `await db.init()` call makes this production-ready without touching any other file.

**Failure modes:** If uvicorn is not running, all frontend requests fail immediately with "Failed to fetch." The error surface to the user is the frontend's connection check, not this file.

**Where it could be improved:** Add startup validation — check that Ollama is reachable, that the cache directory exists and is writable, and that the config loaded correctly. Currently, these failures surface mid-request rather than at startup.

---

### config.py
**Location:** `backend/app/config.py`
**Purpose:** Load and validate all environment configuration from `.env` using pydantic-settings.
**Why it exists:** Centralizing config prevents env var typos from causing runtime errors in the middle of a run. Pydantic validates types at startup.
**Inputs:** `.env` file and OS environment variables.
**Outputs:** A singleton `Settings` instance imported by other modules as `from app.config import settings`.
**Key functions/classes:**
- `Settings(BaseSettings)` — pydantic-settings model. Fields: `ollama_base_url` (default `http://localhost:11434`), `ollama_model` (default `qwen2.5:7b`), `gemini_api_key` (optional str), `anthropic_api_key` (optional str), `database_url` (default `sqlite:///./data/meridian.db`), `synthesizer_provider` (default `ollama`), `cache_dir` (default `data/cache/llm`).
- `settings = Settings()` — module-level singleton.

**The non-obvious choice:** `gemini_api_key`, `anthropic_api_key`, `database_url`, and `synthesizer_provider` are all defined but none of them are consumed by any active code path. They exist to signal intent — the config is the contract for what the system will support when those code paths are built. This is a reasonable pattern for an MVP: define the config surface early, wire the implementation later.

**Failure modes:** If `.env` is missing and a required field has no default, pydantic-settings raises a `ValidationError` at import time, crashing the server before it starts. All current fields have defaults, so this does not happen in practice.

**Where it could be improved:** Add a `validate_config()` function that checks cross-field consistency (e.g., if `synthesizer_provider=gemini` then `gemini_api_key` must not be None) and call it from the lifespan hook.

---

### logging.py
**Location:** `backend/app/logging.py`
**Purpose:** Configure structured logging for the backend.
**Why it exists:** `print()` statements don't include timestamps, log levels, or context. Structured logs (JSON or key=value format) are parseable by log aggregation tools and grep-friendly in dev.
**Inputs:** Called once at application startup via import.
**Outputs:** Configures the root logger or structlog processors.
**Key functions/classes:** Sets up structlog or stdlib logging with consistent format across all modules. Modules elsewhere import `logger = logging.getLogger(__name__)` or `logger = structlog.get_logger()`.

**The non-obvious choice:** Using structlog over stdlib logging is an architectural choice that matters more at scale. In this MVP the difference is cosmetic, but structlog's processor pipeline (add timestamp, add log level, serialize to JSON) is the right pattern to establish early.

**Failure modes:** If logging is misconfigured, errors are swallowed silently. Current logging is functional but not comprehensive — many agent failures log at WARNING rather than ERROR.

**Where it could be improved:** Add request-scoped context (company name, ticker, run ID) to every log line within a run so post-hoc debugging can filter by run.

---

### api/runs.py
**Location:** `backend/app/api/runs.py`
**Purpose:** The real SSE endpoint — receives a company/ticker, streams agent lifecycle events and the final memo.
**Why it exists:** This is the only active API surface the frontend uses. Everything the frontend knows about a run comes through this endpoint.
**Inputs:** Query params `company` (str) and `ticker` (str) on `GET /api/runs/stream`.
**Outputs:** `StreamingResponse` with `Content-Type: text/event-stream`, SSE-formatted JSON frames.
**Key functions/classes:**
- `stream_run(company, ticker)` — the route handler. Calls `run_all(company, ticker)` from `orchestrator/runner.py` and iterates the async generator, formatting each yielded dict as `data: {json}\n\n`.
- `_sse(data)` — helper that serializes a dict to SSE format using `json.dumps(data, default=str)`. The `default=str` is critical — it handles `datetime` objects in `Citation.fetched_at` that survive `dataclasses.asdict()`.

**The non-obvious choice:** `default=str` in `json.dumps`. Without it, `Citation.fetched_at` (a `datetime` object) raises `TypeError: Object of type datetime is not JSON serializable` mid-stream. The stream breaks, the client gets a partial response and hangs. `default=str` converts unserializable objects to their string representation — safe for datetimes, acceptable for this MVP.

**Failure modes:** If `run_all()` raises an unhandled exception, the `StreamingResponse` silently closes. The client's `EventSource` receives an incomplete stream and will retry (EventSource auto-reconnects by default). This creates a retry loop. The frontend does not currently handle this — it would show a spinner indefinitely.

**Where it could be improved:** Send an explicit `event: error` SSE frame before closing on exception. The frontend can then display a meaningful error state rather than hanging.

---

### api/events.py
**Location:** `backend/app/api/events.py`
**Purpose:** Phase 2 artifact — contains a dead `/demo/stream` stub.
**Why it exists:** It was scaffolded during Phase 2 as a placeholder for SSE before the real orchestrator was built. The real SSE endpoint was built in `runs.py` instead.
**Inputs:** None actively consumed.
**Outputs:** The stub returns a hardcoded sequence of fake events — useful for frontend development without a running backend.
**Key functions/classes:** `demo_stream()` — async generator that yields fake `agent_started`, `agent_done`, `memo_ready` events with `asyncio.sleep()` delays.

**The non-obvious choice:** Leaving the stub in the codebase is not an accident — it is useful for frontend development without a running Ollama instance. In a production codebase it would be gated behind a `DEBUG` flag or removed. Here it lives at a different route (`/api/demo/stream`) so it does not conflict.

**Failure modes:** None — it is not called by any active code path.

**Where it could be improved:** Move to a test fixture or a `DEBUG`-gated route. Its presence in `events.py` while the real endpoint is in `runs.py` violates the principle that file names should describe their contents.

---

### llm/client.py
**Location:** `backend/app/llm/client.py`
**Purpose:** Single interface for all LLM calls — checks cache, calls Ollama, writes cache.
**Why it exists:** Every agent needs to call the LLM. Centralizing this means cache logic, retry logic, and model configuration live in one place. Agents do not know which LLM they are calling.
**Inputs:** `model` (str), `prompt` (str), `system` (optional str), `json_mode` (bool).
**Outputs:** Raw LLM response string.
**Key functions/classes:**
- `complete(model, prompt, system, json_mode)` — async function. Computes cache key, checks cache, on miss POSTs to `{ollama_base_url}/api/generate`, writes response to cache, returns response text.
- Cache key: `sha256(f"{model}|{system or ''}|{prompt}|{json_mode}")` — all four inputs contribute. Changing any input (including json_mode) produces a different cache key.

**The non-obvious choice:** `json_mode` is included in the cache key even though it is a boolean. This matters because Ollama's JSON mode actually changes the response format — the same prompt with `json_mode=True` produces different output than with `json_mode=False`. Keying on it correctly ensures cache hits only when the full call signature matches.

**Failure modes:** If Ollama is not running, `aiohttp.ClientConnectorError` raises and propagates up to the agent, which catches it and returns an error `AgentResult`. If Ollama returns a non-200 response, the error is logged and propagated.

**Where it could be improved:** Add exponential backoff retry for transient Ollama failures. Currently, one bad HTTP response fails the agent permanently. Also: Gemini and Anthropic clients are config-ready but not implemented — the `complete()` function has no routing logic.

---

### llm/cache.py
**Location:** `backend/app/llm/cache.py`
**Purpose:** SHA-256 content-addressed disk cache for LLM responses.
**Why it exists:** LLM calls are the slowest and most expensive operation in the system. Caching them means every re-run of the same company (same prompt, same model) returns instantly. This makes development fast and evaluation runs cheap after the first run.
**Inputs:** Cache key (SHA-256 hex string), response string (on write).
**Outputs:** Cached response string (on read), None (on miss).
**Key functions/classes:**
- `get(key)` — async. Reads `{cache_dir}/{key}.json`, returns the `response` field if found.
- `set(key, prompt, model, response)` — async. Writes a JSON file with fields: `prompt_hash`, `model`, `prompt`, `response`, `created_at`.
- File I/O uses `aiofiles` for non-blocking reads and writes.

**The non-obvious choice:** The cache is permanent and never evicted. There is no TTL, no LRU eviction, no size limit. This is intentional for an eval system where reproducibility matters more than freshness. The same cache hit from six months ago will still fire today. For a production system this would be wrong — financial data ages. For a benchmark demo system, it is correct.

**Failure modes:** If `cache_dir` does not exist and is not created at startup, every `set()` call raises `FileNotFoundError`. The directory must exist before the first LLM call. If the cache file is corrupted (partial write, disk full), `get()` raises `json.JSONDecodeError` and the cache miss falls through to a live call.

**Where it could be improved:** Add cache size reporting (how many entries, total disk usage) to the `/health` endpoint. Add optional TTL parameter for cases where data freshness matters.

---

### llm/schemas.py
**Location:** `backend/app/llm/schemas.py`
**Purpose:** Base Pydantic schema for all LLM outputs, and `parse_response()` with a one-retry mechanism.
**Why it exists:** LLMs produce unreliable JSON. Without validation, a malformed response crashes the agent. Without retry, a one-time parse failure fails the whole run. This module makes LLM output handling robust.
**Inputs:** Raw LLM response string, target Pydantic model class.
**Outputs:** Validated Pydantic model instance.
**Key functions/classes:**
- `LLMOutputBase(BaseModel)` — base class. All agent output schemas inherit from this.
- `parse_response(response_text, schema_class)` — tries `schema_class.model_validate_json(response_text)`. On `ValidationError` or `JSONDecodeError`: builds a concrete example from the schema (replacing field type annotations with placeholder values like `"<string>"`, `0.0`, `[]`), injects the example as a hint into a new prompt, retries once via `complete()`. If the retry fails, raises permanently.

**The non-obvious choice:** The retry prompt includes a concrete example, not an abstract schema description. `{"revenue": "<string>"}` is more useful to an LLM than `{"revenue": "str"}`. This insight — that LLMs respond better to concrete examples than type signatures — cut parse failures from ~12% to ~1%. It is also a good interview answer about prompt engineering pragmatics.

**Failure modes:** If the retry also produces invalid JSON, the exception propagates to the agent, which catches it and returns an error `AgentResult` with `skip_critic=True`. The run continues with the other agents.

**Where it could be improved:** Log the original and retry prompts + responses to a separate debug log for post-hoc analysis of failure patterns. Currently, failures are logged but the full context is lost.

---

### sources/bse.py
**Location:** `backend/app/sources/bse.py`
**Purpose:** Fetch stock data for Indian companies using yfinance.
**Why it exists:** Provides structured financial data (price, revenue, margins, debt ratios, officers) without requiring a paid data vendor.
**Inputs:** Ticker symbol string (e.g., "RELIANCE").
**Outputs:** Dict of stock info fields from yfinance.
**Key functions/classes:**
- `fetch_stock_data(ticker)` — async wrapper. Appends `.NS` suffix, creates `yf.Ticker`, calls `.info` in a thread executor via `asyncio.get_event_loop().run_in_executor(None, ...)`. Returns the info dict.
- Tries `.NS` (NSE) first; falls back to `.BO` (BSE) if the NSE ticker returns no data.

**The non-obvious choice (and divergence):** Despite being named `bse.py` and described as a BSE data source, this module has zero connection to BSE's official API. It calls Yahoo Finance. The name is a misnomer inherited from the planning phase. In an interview, be honest: "I named it bse.py because that was the intent, but I used yfinance because it supports Indian tickers natively and requires no API key."

**Failure modes:** If the ticker is invalid or not listed, yfinance returns an empty dict. Agents that receive an empty dict produce findings with placeholder values or raise KeyError, which the agent catches. If yfinance's servers are rate-limiting, requests silently time out.

**Where it could be improved:** Add ticker validation before the yfinance call. Cache yfinance responses (currently only LLM responses are cached — the same ticker hits yfinance on every run). The people agent makes a separate yfinance call for the same ticker the financial agent already fetched, which is a double-fetch for no reason.

---

### sources/wikipedia.py
**Location:** `backend/app/sources/wikipedia.py`
**Purpose:** Fetch a Wikipedia article summary for a company.
**Why it exists:** Wikipedia provides company history, founding date, business description, and founding figures — context that yfinance does not provide.
**Inputs:** Company name string.
**Outputs:** Summary text string (first N paragraphs of the Wikipedia article).
**Key functions/classes:**
- `fetch_summary(company_name)` — async wrapper around `wikipediaapi.Wikipedia().page(company_name).summary`. Runs in thread executor.

**The non-obvious choice:** Using the article summary rather than the full text. Full articles for major Indian companies can be very long — more than the context window for `qwen2.5:7b`. The summary is the right tradeoff: dense, accurate, fits in prompt.

**Failure modes:** If the page does not exist (`page.exists() == False`), returns an empty string. If the company name does not match a Wikipedia page title, returns empty. The financial and people agents handle empty strings gracefully (the LLM prompt notes "no Wikipedia data available").

**Where it could be improved:** Try alternative page titles if the primary fails (e.g., "Reliance Industries Limited" if "Reliance Industries" has no page). Add disambiguation handling.

---

### sources/reddit.py
**Location:** `backend/app/sources/reddit.py`
**Purpose:** Fetch Reddit mentions of a company from Indian investing subreddits.
**Why it exists:** Reddit is the most accessible source of retail investor sentiment for Indian companies. No API key is required for the public JSON API.
**Inputs:** Company name string, list of subreddits to search.
**Outputs:** List of post dicts with title, selftext, score, num_comments, url.
**Key functions/classes:**
- `fetch_mentions(company_name, subreddits)` — async. Hits `https://www.reddit.com/r/{sub}/search.json?q={company_name}&sort=relevance&limit=25` for each subreddit, collects results.
- Uses `aiohttp.ClientSession` with a browser User-Agent header (Reddit rate-limits bots aggressively).

**The non-obvious choice:** Using the public JSON API instead of PRAW (the official Reddit Python library). PRAW requires OAuth credentials. The public JSON endpoint requires only a non-bot User-Agent. For a zero-budget project, this is the right call.

**Failure modes:** Reddit rate-limits aggressively. A 429 response silently returns an empty list. If the subreddit returns no results for the company name, `customer.py` short-circuits with `skip_critic=True`. If `aiohttp` times out, the customer agent returns an error result.

**Where it could be improved:** Add retry-after handling for 429 responses. Add results from more subreddits (currently limited to a few Indian investing communities).

---

### sources/news.py
**Location:** `backend/app/sources/news.py`
**Purpose:** Fetch recent news articles about a company via Google News RSS.
**Why it exists:** Recent news provides context that yfinance and Wikipedia do not — earnings announcements, regulatory actions, product launches, scandals. No API key required.
**Inputs:** Company name string.
**Outputs:** List of article dicts with title, link, published date.
**Key functions/classes:**
- `fetch_news(company_name)` — async. Hits `https://news.google.com/rss/search?q={company_name}+India+stock&hl=en-IN&gl=IN&ceid=IN:en`, parses XML response using `xml.etree.ElementTree`.

**The non-obvious choice (and divergence from planning):** PLANNING.md implied NewsAPI. This implementation uses Google News RSS, which requires no API key and has no rate limit that has been hit in testing. The trade-off: Google News RSS has less structured metadata than NewsAPI, and there is no way to filter by date precisely.

**Important implementation note:** News articles are fetched by the financial agent but are NOT passed to the LLM prompt. They go directly to the citations list. This means news does not influence the LLM's financial analysis — it only appears as a citation in the memo. This is intentional: including news headlines in the prompt would change the cache hash for every company whenever the news changes, breaking the cache.

**Failure modes:** If Google News is unavailable, returns an empty list. The financial agent handles this gracefully.

**Where it could be improved:** Include news snippets in the LLM prompt (with a separate cache key that includes the news fetch date) to make the analysis more current. Currently the financial analysis is grounded only in yfinance + Wikipedia data.

---

### agents/base.py
**Location:** `backend/app/agents/base.py`
**Purpose:** Shared data structures and the abstract base class for all agents.
**Why it exists:** Without a common interface, the orchestrator cannot call agents polymorphically. Without shared data structures, the critic and synthesizer cannot process results uniformly.
**Inputs:** N/A (base classes and dataclasses).
**Outputs:** N/A.
**Key functions/classes:**
- `Citation` — dataclass. Fields: `source` (str, e.g., "yfinance"), `url` (str), `label` (str, display text), `snippet` (str, short excerpt), `fetched_at` (datetime).
- `Finding` — dataclass. Fields: `label` (str), `value` (str), `flagged` (bool, default False). Flagged findings are highlighted in the memo with a warning indicator.
- `AgentResult` — dataclass. Fields: `agent_name` (str), `findings` (list[Finding]), `citations` (list[Citation]), `confidence` (float 0.0–1.0), `skip_critic` (bool, default False), `error` (optional str).
- `Agent` — abstract base class (ABC). Requires subclasses to implement `run(ticker: str, company_name: str) -> AgentResult`.

**The non-obvious choice:** `skip_critic` is on `AgentResult`, not on the agent class. This means the same agent can set `skip_critic=True` conditionally (based on data quality) rather than being statically excluded. The customer agent uses this: it sets `skip_critic=True` when fewer than 3 relevant Reddit posts are found, because the findings are pre-determined boilerplate ("insufficient data"), not LLM claims.

**Failure modes:** If a subclass does not implement `run()`, Python raises `TypeError` at instantiation time. This is the correct behavior — fail fast at import time, not mid-run.

**Where it could be improved:** Add a `metadata` dict field to `AgentResult` for agent-specific diagnostic data (e.g., how many Reddit posts were found, what ticker suffix was used). Currently this information is lost after the agent returns.

---

### agents/financial.py
**Location:** `backend/app/agents/financial.py`
**Purpose:** Gather financial data and produce structured financial findings.
**Why it exists:** Financial metrics are the foundation of any investment memo. This agent provides revenue, margins, debt, and growth data with citations.
**Inputs:** `ticker` (str), `company_name` (str).
**Outputs:** `AgentResult` with financial findings and citations from yfinance, Wikipedia, and news.
**Key functions/classes:**
- `FinancialAgent.run()` — fetches yfinance data, Wikipedia summary, and news articles concurrently via `asyncio.gather(fetch_stock_data(...), fetch_summary(...), fetch_news(...))`.
- `_build_prompt(stock_data, wiki_summary)` — constructs the LLM prompt from yfinance and Wikipedia data only (news is excluded from the prompt — see note in sources/news.py deep dive).
- `FinancialOutput(LLMOutputBase)` — Pydantic schema for the expected LLM response. Fields: revenue, gross_margin, net_margin, debt_to_equity, findings list, confidence.

**The non-obvious choice:** `asyncio.gather` for the three source fetches. This means yfinance, Wikipedia, and news all run concurrently rather than sequentially. For a run where all three sources respond in ~2 seconds, sequential would take ~6 seconds; parallel takes ~2 seconds. Multiplied across four agents, this matters.

**Failure modes:** If yfinance returns no data for the ticker, `_build_prompt` receives an empty dict and the LLM prompt contains "no financial data available." The LLM typically produces low-confidence findings with a note about data unavailability. The agent still returns a result — it does not raise.

**Where it could be improved:** Cache yfinance responses to disk (currently only LLM responses are cached). Pass news headlines to the LLM prompt as a separate section with its own cache TTL.

---

### agents/market.py
**Location:** `backend/app/agents/market.py`
**Purpose:** Assess market position, sector, and competitive context.
**Why it exists:** Investors need to know whether a company is growing faster or slower than its sector, who the main competitors are, and what the market dynamics look like.
**Inputs:** `ticker` (str), `company_name` (str).
**Outputs:** `AgentResult` with market/sector findings.
**Key functions/classes:**
- `MarketAgent.run()` — fetches yfinance data only (no Wikipedia, no news). Builds a prompt focused on sector, P/E ratio, market cap, 52-week range, beta, volume.
- `MarketOutput(LLMOutputBase)` — sector, market_cap, pe_ratio, competitors, growth_rate, findings list, confidence.

**The non-obvious choice:** Market agent uses only yfinance, not Wikipedia. This is a deliberate scope decision — the market section is about quantitative data, not qualitative history. Wikipedia's company article rarely contains useful competitive intelligence anyway.

**Failure modes:** yfinance often returns None for P/E ratio and beta for Indian mid-caps that are not well-covered on Yahoo Finance. The LLM handles None values by noting "data not available" in findings. The market agent has the second-highest hallucination rate (20% avg, 50% worst case) — likely because it asks the LLM to infer competitive context from limited yfinance data.

**Where it could be improved:** Add a sector-comparison data source — fetch 2-3 competitor tickers from yfinance and include comparative metrics in the prompt.

---

### agents/people.py
**Location:** `backend/app/agents/people.py`
**Purpose:** Profile the leadership team — CEO, CFO, key officers, tenure, background.
**Why it exists:** Management quality is a key factor in investment decisions. yfinance provides officer names; Wikipedia provides background context.
**Inputs:** `ticker` (str), `company_name` (str).
**Outputs:** `AgentResult` with leadership findings.
**Key functions/classes:**
- `PeopleAgent.run()` — calls `yf.Ticker(ticker).info` directly (not via `sources/bse.fetch_stock_data`) plus `fetch_summary()`. Extracts `companyOfficers` from the info dict.
- `PeopleOutput(LLMOutputBase)` — ceo_name, cfo_name, officers list, tenure_assessment, findings list, confidence.

**The non-obvious choice (and a bug):** `PeopleAgent` calls `yf.Ticker(ticker).info` directly rather than reusing `sources/bse.fetch_stock_data()`. This means the same ticker hits yfinance twice per run — once for the financial agent, once for the people agent. The yfinance call is not cached (only LLM responses are cached), so this is a real double-fetch on every run. It is not catastrophic (yfinance is fast and free), but it is wasteful and inconsistent.

**Failure modes:** `companyOfficers` is sometimes empty or missing from yfinance for smaller Indian companies. The people agent handles this by noting "officer data not available" and producing low-confidence findings. People agent has the highest hallucination rate (29% avg, 60% worst) — the LLM fills gaps in officer data with plausible-sounding but unverifiable claims.

**Where it could be improved:** Reuse financial agent's cached yfinance result. Add LinkedIn or Crunchbase as a source for officer background. The current Wikipedia-based approach for leadership background is limited.

---

### agents/customer.py
**Location:** `backend/app/agents/customer.py`
**Purpose:** Assess customer and retail investor sentiment from Reddit discussions.
**Why it exists:** Qualitative sentiment from actual customers and retail investors provides a signal that does not appear in financial statements.
**Inputs:** `ticker` (str), `company_name` (str).
**Outputs:** `AgentResult` with sentiment findings; `skip_critic=True` if fewer than 3 relevant posts.
**Key functions/classes:**
- `CustomerSentimentAgent.run()` — fetches Reddit mentions, calls `_filter_relevant()`, checks count, either short-circuits or calls LLM.
- `_filter_relevant(posts, company_name)` — checks if company name (or its first word) appears in `title + selftext`. Returns only posts that mention the company.
- Short-circuit condition: `if len(relevant_posts) < 3`: returns pre-determined findings ("Insufficient Reddit data for sentiment analysis"), citations are empty, `skip_critic=True`.
- When calling LLM: passes `all_posts` (not `relevant_posts`) to preserve the cache hash. This is the correct behavior — using `relevant_posts` would produce a different cache key each time the filter result changes, breaking the cache for runs where the post set is the same but the filter is slightly different.

**The non-obvious choice:** Passing `all_posts` to the LLM even though `_filter_relevant` found relevant posts. The reason: `relevant_posts` is a dynamic subset — if one post gets deleted between runs, the subset changes, the cache key changes, and the LLM call reruns. Using `all_posts` makes the cache key stable as long as Reddit returns the same posts. The LLM prompt instructs it to focus on the company in question.

**Failure modes:** If Reddit is rate-limited, `fetch_mentions` returns empty and the agent short-circuits with "insufficient data." If the LLM returns sentiment that contradicts the actual posts, the critic would flag it — but since `skip_critic=True` is set for the short-circuit case (not for the LLM case), real LLM output does go through the critic.

**Where it could be improved:** Add more subreddits (economic news, sector-specific communities). Use a sentiment classification model rather than an LLM for this task — classifying positive/negative/neutral is a well-solved NLP problem that does not require a generative model.

---

### agents/critic.py
**Location:** `backend/app/agents/critic.py`
**Purpose:** Score each agent's findings for hallucination likelihood in a separate pass.
**Why it exists:** Without post-hoc verification, there is no way to distinguish confident correct findings from confident hallucinations. The critic provides a calibrated signal about claim reliability.
**Inputs:** List of `AgentResult` objects.
**Outputs:** `CriticResult` with per-finding scores and overall `hallucination_rate`.
**Key functions/classes:**
- `CriticResult` — dataclass. Fields: `scores` (dict mapping finding label to float 0.0–1.0), `hallucination_rate` (float), `flagged_findings` (list[str]).
- `run_critic(results)` — async. Filters `eligible = [r for r in results if not r.skip_critic]`. Scores each eligible result in parallel via `asyncio.gather`. Computes `hallucination_rate = mean(all_scores)`.
- `_EXCLUDED_FROM_CRITIC = {"confidence", "error"}` — fields excluded from scoring. These are meta-fields that appear in agent output but are not factual claims the critic should evaluate.

**The non-obvious choice:** The critic runs per-`AgentResult`, not per-finding globally. This means the critic for the financial agent sees only financial findings, not the full set. This is intentional — the financial critic call includes the financial agent's citations as context, so it can evaluate claims against the cited evidence. A global critic call would dilute this context.

**Failure modes:** If the critic LLM call fails for one agent, that agent's findings get no score and the overall hallucination rate is computed only from successful scores. If the critic scores everything at 0.0 (no hallucination), the memo looks cleaner than it should. If it scores everything at 1.0 (all hallucination), the memo is plastered with warnings and loses credibility.

**Where it could be improved:** The critic currently asks the LLM to score claims without providing the original data sources as ground truth. A stronger critic would compare each claim against the raw fetched data (yfinance numbers, Wikipedia text) rather than relying on the LLM's training knowledge.

---

### orchestrator/planner.py
**Location:** `backend/app/orchestrator/planner.py`
**Purpose:** Decide which agents to run for a given company.
**Why it exists:** In a more sophisticated system, different company types require different agents. A startup might not need a financial agent (no public financials). A software company might not need a market agent (sector dynamics are different). The planner is the policy layer.
**Inputs:** `ticker` (str), `company_name` (str).
**Outputs:** List of `Agent` instances.
**Key functions/classes:**
- `agents_for(ticker, company_name)` — returns all four agents, always. No conditional logic currently.

**The non-obvious choice:** Despite having a planner at all (many simpler systems hardcode the agent list in the runner), the current implementation always returns all four. The value of having a planner is not what it does now, but what it makes possible: adding a fifth agent, making agent selection company-type-aware, or A/B testing different agent configurations — all require changing only this file.

**Failure modes:** None currently — the function cannot fail. If agents required initialization parameters that could fail, this would be the place to handle that.

**Where it could be improved:** Add company-type detection (listed company vs. startup, sector classification) and adjust the agent set accordingly. Add support for a "quick mode" that runs only financial + market for speed.

---

### orchestrator/runner.py
**Location:** `backend/app/orchestrator/runner.py`
**Purpose:** Concurrently execute all agents, stream lifecycle events, run the critic, run the synthesizer, yield the completed memo.
**Why it exists:** This is the heart of the orchestration layer. It bridges the concurrent agent execution model with the sequential SSE stream the frontend expects.
**Inputs:** `company_name` (str), `ticker` (str).
**Outputs:** Async generator yielding event dicts.
**Key functions/classes:**
- `run_all(company_name, ticker)` — async generator. The full sequence:
  1. Get agents from planner.
  2. Create `asyncio.Queue`.
  3. Define `run_one(agent)` — calls `agent.run()`, puts `agent_started` then `agent_done` into queue.
  4. `tasks = [asyncio.create_task(run_one(a)) for a in agents]`.
  5. `for _ in range(len(agents) * 2): yield await queue.get()` — yields exactly 2 events per agent.
  6. `results = await asyncio.gather(*tasks)` — collects all results.
  7. Run critic, yield `critic_done`.
  8. Run synthesizer, yield `memo_ready`.

**The non-obvious choice:** The `asyncio.Queue` pattern is the key design decision here. The alternative — yielding directly from agent coroutines — would require a more complex fan-in mechanism. The queue provides a clean interface: agents produce events independently and concurrently; the generator consumes them in whatever order they arrive. The `range(len(agents) * 2)` bound is exact because each agent produces exactly 2 events (started + done).

**Failure modes:** If one agent raises an unhandled exception inside `run_one()`, `asyncio.gather(*tasks)` will re-raise it after all tasks complete (or immediately if `return_exceptions=False`, which is the default). This means one bad agent can delay the critic and synthesizer. Mitigation: `run_one()` should catch all exceptions and return an error `AgentResult` rather than raising.

**Where it could be improved:** Use `return_exceptions=True` in `asyncio.gather` and handle error results explicitly rather than letting exceptions propagate. Add a timeout per agent so a hung Ollama call does not block the entire run.

---

### synthesizer/memo.py
**Location:** `backend/app/synthesizer/memo.py`
**Purpose:** Assemble all agent results and critic scores into a structured markdown memo.
**Why it exists:** Without synthesis, the user would see four separate agent dumps. The synthesizer creates a coherent, readable document with consistent structure, deduplicated citations, and critic annotations.
**Inputs:** List of `AgentResult` objects, `CriticResult`.
**Outputs:** Markdown string.
**Key functions/classes:**
- `build_memo(results, critic_result)` — iterates through `SECTIONS` order, finds the matching `AgentResult` for each section, formats findings using `FIELD_LABELS`, appends citations, deduplicates via `seen: set[str]`.
- Citation deduplication: `seen` is keyed on `f"{c.source}:{c.label}"`. First occurrence of each unique (source, label) pair wins; subsequent duplicates are dropped. The financial and people agents both fetch Wikipedia summaries, so the Wikipedia citation for a company would appear twice without deduplication.

**The non-obvious choice (and divergence):** `synthesizer_provider` config field is read by config.py but `build_memo()` does not read it. The synthesizer is always Ollama, regardless of config. This means the planned "use Gemini for synthesis, Ollama for agents" architecture (which would have been interview-gold as a tiered-quality system) was never wired. The memo quality is thus limited by `qwen2.5:7b`'s synthesis capability.

**Failure modes:** If all agents return error results, the memo contains mostly "data unavailable" placeholders. If the critic result is None (critic failed entirely), the memo skips the critic section rather than crashing.

**Where it could be improved:** Wire `synthesizer_provider` to actually route to Gemini or Anthropic. Add a "confidence section" at the top of the memo that summarizes the overall hallucination rate and flags any sections with high hallucination scores.

---

### synthesizer/templates.py
**Location:** `backend/app/synthesizer/templates.py`
**Purpose:** Define the canonical section order and field label display names for the memo.
**Why it exists:** Without a canonical order, sections would appear in whatever order agents finished. Consistent structure makes the memo scannable and professional.
**Inputs:** N/A (constants).
**Outputs:** `SECTIONS` (list of section names), `FIELD_LABELS` (dict mapping internal field names to display strings).
**Key functions/classes:**
- `SECTIONS` — ordered list: `["Financial Analysis", "Market Position", "Leadership & People", "Customer Sentiment"]`.
- `FIELD_LABELS` — maps snake_case field names to display labels (e.g., `"gross_margin"` → `"Gross Margin"`).

**The non-obvious choice:** Keeping templates as pure data (no logic) rather than template strings or Jinja templates. This makes the section structure easy to reorder or extend without parsing template syntax.

**Failure modes:** If an agent name does not match an entry in `SECTIONS`, the synthesizer skips that agent's section. This is a silent failure — the memo appears complete but is missing a section.

**Where it could be improved:** Add section-level metadata (e.g., which agent feeds each section, which fields are required vs. optional) to make the template more self-describing.

---

### store/
**Location:** `backend/app/store/`
**Purpose:** Planned persistence layer — SQLite database for runs, results, and citations.
**Why it exists:** It does not currently exist in any meaningful sense. The directory contains only an empty `__init__.py`.

**Divergence from PLANNING.md — this is the biggest gap in the codebase.**

PLANNING.md specified: `store/models.py` (SQLModel table definitions for Run, AgentResult, Citation), `store/db.py` (database connection and session management), `store/repository.py` (CRUD operations). The ADR-002 decision selected SQLite with the migration path to Postgres via connection string change.

None of this was built. The system is fully stateless. Every run exists only in:
1. The SSE stream (in-flight, gone once the connection closes)
2. The client's React `useReducer` state (gone on page refresh)
3. The LLM cache on disk (the response exists, but no structured metadata about the run)

**What this means in practice:**
- Refreshing the run page loses all state — the user sees an empty memo viewer.
- There is no way to list previous runs.
- There is no way to compare two runs for the same company.
- The eval framework saves results to `data/eval/results.json` directly (bypassing any store) as a workaround.

**What would need to be built:**
- `store/models.py`: `Run` table (id, company, ticker, status, created_at), `AgentResultRow` table (FK to Run), `CitationRow` table (FK to AgentResultRow).
- `store/db.py`: SQLModel `create_engine`, async session factory.
- `store/repository.py`: `create_run()`, `update_run_status()`, `save_agent_result()`, `get_run(id)`, `list_runs()`.
- `api/runs.py` update: create a Run row at request time, save each AgentResult as it completes, update status to "complete" at the end.
- `app/runs/[id]/page.tsx` update: load memo from API on mount (not just from SSE state) so page refresh works.
- `main.py` lifespan update: call `SQLModel.metadata.create_all(engine)` at startup.

**Failure modes:** Not applicable (no code to fail). The absence itself is a failure mode: any unexpected server restart or client disconnect loses the run permanently.

---

### eval/benchmark.py
**Location:** `backend/app/eval/benchmark.py`
**Purpose:** CLI runner that executes the full Meridian pipeline against a ground-truth dataset and saves metrics.
**Why it exists:** Without automated evaluation, there is no objective measure of system quality. The benchmark allows comparing changes (model swap, prompt update, new agent) against a baseline.
**Inputs:** Dataset files from `eval/dataset/*.json`, CLI arguments (which companies to run, whether to include baseline).
**Outputs:** `data/eval/results.json`, `data/eval/report.md`.
**Key functions/classes:**
- `run_system(company, ticker)` — calls the full pipeline (planner + runner + critic + synthesizer) and returns results.
- `load_dataset()` — reads all `.json` files from `eval/dataset/`, returns list of company dicts.
- Main loop: for each company, run system, compute metrics, aggregate.

**The non-obvious choice:** Running the full pipeline (including LLM calls) for each company. After the first run, all LLM calls hit the cache, so subsequent eval runs are near-instant. The cache is what makes the eval framework practical — without it, running 15 companies through 4 agents + critic each would take hours.

**Failure modes:** If a company's LLM responses are cached from a different model version, the cache hits return stale responses. If `data/eval/results.json` is from a partial run (server crash mid-eval), it is overwritten on the next full run. If a dataset file is malformed, the eval fails for that company and continues.

**Where it could be improved:** Add parallel company evaluation (currently sequential). Add incremental results saving (write after each company rather than at the end) to avoid losing progress on crashes.

---

### eval/metrics.py
**Location:** `backend/app/eval/metrics.py`
**Purpose:** Compute all evaluation metrics from a set of AgentResults and ground-truth claims.
**Why it exists:** Raw findings are not evaluable — they need to be reduced to numbers that can be compared across runs, models, and configurations.
**Inputs:** List of `AgentResult` objects, list of ground-truth claim strings, `CriticResult`.
**Outputs:** Dict of metric name → value.
**Key functions/classes:**
- `hallucination_rate(critic_result)` — returns `critic_result.hallucination_rate` directly.
- `citation_count(results)` — total citations across all agents (after deduplication).
- `finding_completeness(results)` — fraction of expected fields that are present and non-empty. Expected fields come from `FIELD_LABELS` in templates.py.
- `per_agent_hallucination(critic_result)` — hallucination rate broken down by agent.
- `source_citation_breakdown(results)` — fraction of citations from each source (yfinance, wikipedia, reddit, news).
- `worst_findings(critic_result, n=3)` — top N findings by hallucination score.
- `ground_truth_coverage(results, gt_claims)` — fraction of GT claims "covered" by findings.
- `_claim_mentioned(claim, findings_text)` — keyword match. Checks if any word >4 chars from the first 6 significant words of the claim appears anywhere in the combined findings text.

**The non-obvious choice:** The `_claim_mentioned` keyword heuristic. This is deliberately simple — no embeddings, no semantic similarity, no NLP. The reasoning: for a 15-company benchmark running locally with zero budget, the overhead of embedding-based similarity (loading a model, computing vectors) is not justified. The keyword heuristic is wrong ~15-20% of the time (synonyms, paraphrases, abbreviations are missed) but it is fast, free, and deterministic.

**Failure modes:** If a GT claim uses different terminology than the findings text (e.g., "operating income" vs. "EBIT"), `_claim_mentioned` returns False and coverage is undercounted. If findings text contains the keyword in an unrelated context, coverage is overcounted.

**Where it could be improved:** Replace `_claim_mentioned` with a sentence-transformers cosine similarity check. This would take coverage accuracy from ~80% to ~95% and would be a meaningful improvement for the eval's validity.

---

### eval/report.py
**Location:** `backend/app/eval/report.py`
**Purpose:** Format evaluation results into a human-readable markdown report.
**Why it exists:** `results.json` is machine-readable but not easily skimmable. The report provides a per-company table, aggregate stats, and worst-case examples.
**Inputs:** Evaluation results dict (loaded from `results.json`).
**Outputs:** Markdown string, written to `data/eval/report.md`.
**Key functions/classes:**
- `generate_report(results)` — formats results into markdown with per-company table, source breakdown table, per-agent hallucination table, worst findings section.

**Failure modes:** If `results.json` has a schema mismatch (partial run, old format), `generate_report` raises KeyError on missing fields.

**Where it could be improved:** Add trend analysis (compare against a locked baseline JSON to show delta). Add a pass/fail threshold (e.g., flag any company where hallucination_rate > 30%).

---

### eval/baseline.py
**Location:** `backend/app/eval/baseline.py`
**Purpose:** Run a single-prompt LLM call (no agents, no tools) on the same dataset for baseline comparison.
**Why it exists:** Comparing Meridian against a naive single-prompt approach demonstrates the value of the multi-agent architecture quantitatively. Without a baseline, the metric numbers have no context.
**Inputs:** Company name, ticker (same as main system).
**Outputs:** Baseline `AgentResult` — same schema as agent output but produced from a single LLM call.
**Key functions/classes:**
- `run_baseline(company_name, ticker)` — builds a single prompt ("you are a financial analyst, write a due diligence memo on {company_name}"), calls `complete()`, extracts sections by keyword search.
- `_extract_section(response_text, keyword)` — finds ~200 characters around a keyword occurrence (e.g., "revenue", "leadership").

**The non-obvious choice:** The baseline uses the same LLM (Ollama/qwen2.5:7b) as the main system. This isolates the architectural contribution of agents + retrieval + critic from the model quality. If the baseline used a stronger model, the comparison would be confounded.

**Failure modes:** `_extract_section` is brittle — if the LLM's response does not include the expected keyword, the section is empty. Baseline citation count is always 0 (no retrieval step). In the latest report, baseline comparison rows were empty (`baseline_rows` was empty in `results.json`) — the baseline may not have been run in the most recent eval pass.

**Where it could be improved:** Make the baseline extraction more robust (parse by section headers rather than keyword search). Ensure baseline always runs alongside the main system in the benchmark loop.
