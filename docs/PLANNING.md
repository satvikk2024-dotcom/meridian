# Meridian — Master Planning Document

> Multi-Agent Due Diligence System
> Phase 0 — Project Planning & Architecture
> Last updated: May 2026

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement & Scope](#2-problem-statement--scope)
3. [The Three-Layer Pitch](#3-the-three-layer-pitch)
4. [System Architecture](#4-system-architecture)
5. [Folder Structure](#5-folder-structure)
6. [Data Flow Walkthrough](#6-data-flow-walkthrough)
7. [Database Schema](#7-database-schema)
8. [Agent Responsibility Matrix](#8-agent-responsibility-matrix)
9. [Evaluation Framework](#9-evaluation-framework)
10. [Caching Strategy](#10-caching-strategy)
11. [Tech Stack & Tooling](#11-tech-stack--tooling)
12. [14-Day Milestone Roadmap](#12-14-day-milestone-roadmap)
13. [Risk Register](#13-risk-register)
14. [Token-Saving Playbook](#14-token-saving-playbook)
15. [Architecture Decision Records (ADRs)](#15-architecture-decision-records-adrs)
16. [Success Criteria](#16-success-criteria)
17. [Resume & Interview Strategy](#17-resume--interview-strategy)
18. [Comprehension Check](#18-comprehension-check)

---

## 1. Executive Summary

**Meridian** is a multi-agent due diligence system that produces structured, citation-backed investment memos on publicly traded U.S. companies in 8-15 minutes.

It is built as a high-impact resume project to demonstrate:

- AI workflow orchestration
- Async system design
- Retrieval pipelines
- Evaluation frameworks
- Citation grounding
- Product thinking
- Clean architecture

**Target audiences for this project:**

- AI startup recruiters
- Technical PM interviewers
- AI-forward enterprise SaaS companies
- Modern AI tooling companies
- Systems-oriented engineering teams

**Build constraints:**

- 2 weeks (~50 hours total)
- Zero monetary spend (free tiers + local models only)
- Solo developer, beginner-to-intermediate level
- Local-first development; simple deployment

---

## 2. Problem Statement & Scope

### 2.1 The Core Problem

VC, PE, and corporate-development analysts spend the first 1-2 weeks of every deal doing mechanical research before any real strategic thinking can begin. This work is repetitive, parallelizable, and a strong fit for AI augmentation — but generic LLMs fail at it because they hallucinate financial figures and cannot cite sources.

### 2.2 What Meridian Does

> **Meridian takes the name of a publicly traded U.S. company and produces a structured diligence memo in 8-15 minutes by orchestrating 4 specialized AI agents that gather evidence from public sources, validate findings via a critic agent, and synthesize a cited report.**

Every word in that sentence is load-bearing:

| Phrase | Why It Matters |
|---|---|
| publicly traded U.S. company | SEC filings are free; no paywalled startup data |
| structured diligence memo | Defined output schema, not free-form text |
| 8-15 minutes | Sets latency budget; drives async + streaming choices |
| 4 specialized agents | Fixed scope — not 12, not 5, four |
| public sources | Zero API costs |
| critic agent | The differentiator — trust calibration |
| cited report | Every claim is traceable to a source |

### 2.3 Explicit Non-Goals

The MVP does **not** support:

- ❌ Private companies (data paywalled)
- ❌ Real-time monitoring or continuous updates
- ❌ User authentication or multi-tenancy
- ❌ Custom or industry-specific memo templates
- ❌ Mobile UI
- ❌ Collaboration features
- ❌ PDF/DOCX export (web view only)
- ❌ User-selectable LLM providers
- ❌ Custom industry verticals

Any urge to add these in week 2 goes into `FUTURE.md`. Not implemented.

---

## 3. The Three-Layer Pitch

Practice each of these out loud until natural.

### 3.1 Ten-Second Pitch

> "Meridian is an AI system that produces a 15-page diligence memo on any public company in under 15 minutes, with every claim cited."

### 3.2 Sixty-Second Pitch

> "VC and PE analysts spend the first week of every deal doing mechanical research before any real thinking starts. Meridian compresses that. You give it a company name; it spawns four specialized AI agents — financial, market, people, and customer sentiment — that gather evidence from SEC filings, news, GitHub, and Reddit in parallel. A critic agent then evaluates each piece of evidence for quality before a synthesizer agent writes a structured memo with full source citations. End-to-end takes about 12 minutes. The hard part isn't the AI — it's the orchestration, the citation grounding, and the evaluation framework that proves it actually works."

### 3.3 Five-Minute Architecture Pitch

Built progressively across Phases 1-11. By the end you can whiteboard the full system from memory.

---

## 4. System Architecture

### 4.1 High-Level Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     USER (browser)                          │
│   types "Stripe" → clicks Run → watches progress stream     │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP POST /api/runs
                             │ SSE GET /api/runs/{id}/events
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                  FRONTEND (Next.js)                         │
│  • Form input                                               │
│  • Live progress feed (SSE consumer)                        │
│  • Memo viewer with hover citations                         │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                BACKEND (FastAPI + asyncio)                  │
│                                                             │
│  ┌──────────────┐                                           │
│  │   Planner    │  decides which agents to run              │
│  └──────┬───────┘                                           │
│         │ spawns                                            │
│         ▼                                                   │
│  ┌────────────────────────────────────────┐                 │
│  │       Agent Pool (parallel)            │                 │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌──┐ │                 │
│  │  │Financial│ │ Market │ │ People │ │CS│ │                 │
│  │  └────┬───┘ └────┬───┘ └────┬───┘ └─┬┘ │                 │
│  └───────┼──────────┼──────────┼───────┼──┘                 │
│          ▼          ▼          ▼       ▼                    │
│  ┌─────────────────────────────────────────┐                │
│  │       Evidence Store (SQLite)           │                │
│  └────────────────┬────────────────────────┘                │
│                   ▼                                         │
│  ┌──────────────┐                                           │
│  │    Critic    │  scores each evidence item                │
│  └──────┬───────┘                                           │
│         ▼                                                   │
│  ┌──────────────┐                                           │
│  │ Synthesizer  │  produces final memo                      │
│  └──────┬───────┘                                           │
│         ▼                                                   │
│  ┌──────────────┐                                           │
│  │  Memo Store  │                                           │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│         LLM LAYER (with cache)                              │
│  Ollama (local, dev) ──┬──→ disk cache                      │
│  Gemini Flash (demo) ──┘                                    │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│         DATA SOURCES (free)                                 │
│  SEC EDGAR  • Wikipedia  • Reddit  • GitHub  • NewsAPI free │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Key Design Choices

| Choice | Rationale |
|---|---|
| Single backend service, no microservices | Beginner-appropriate; recruiters don't expect microservices from a 2-week solo project. Splitting prematurely is "enterprise theater." |
| SQLite for MVP, not Postgres | Zero setup. Single file. Swap to Postgres in Phase 10 if hosting requires it. |
| asyncio, not Celery/Redis | One process. Easy to reason about. Celery is overkill. |
| Server-Sent Events (SSE), not WebSockets | One-way push is exactly what we need. SSE is simpler. |
| In-process queue (asyncio), not external | One less moving part. Recruiters care about agent design, not queue choice. |
| Disk-based LLM cache | Eliminates ~90% of dev API costs. |
| Local Ollama for dev, free Gemini Flash for final demo | True zero-cost dev loop; better-quality final output. |

---

## 5. Folder Structure

```
meridian/
├── README.md
├── FUTURE.md                    ← park scope-creep ideas here
├── .gitignore
├── .env.example
│
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py              ← FastAPI entrypoint
│   │   ├── config.py            ← env var loading
│   │   ├── logging.py           ← structured logger setup
│   │   │
│   │   ├── api/
│   │   │   ├── runs.py          ← POST /runs, GET /runs/{id}
│   │   │   └── events.py        ← SSE stream
│   │   │
│   │   ├── llm/
│   │   │   ├── client.py        ← unified LLM interface
│   │   │   ├── cache.py         ← disk cache for LLM calls
│   │   │   └── schemas.py       ← Pydantic structured output
│   │   │
│   │   ├── agents/
│   │   │   ├── base.py          ← Agent abstract class
│   │   │   ├── financial.py
│   │   │   ├── market.py
│   │   │   ├── people.py
│   │   │   ├── customer.py
│   │   │   └── critic.py
│   │   │
│   │   ├── orchestrator/
│   │   │   ├── planner.py
│   │   │   └── runner.py        ← async parallel execution
│   │   │
│   │   ├── synthesizer/
│   │   │   ├── memo.py
│   │   │   └── templates.py
│   │   │
│   │   ├── sources/             ← data fetchers
│   │   │   ├── sec.py
│   │   │   ├── wikipedia.py
│   │   │   ├── reddit.py
│   │   │   ├── github.py
│   │   │   └── news.py
│   │   │
│   │   ├── store/
│   │   │   ├── models.py        ← SQLModel / SQLAlchemy
│   │   │   ├── db.py            ← engine, session
│   │   │   └── repository.py    ← data access layer
│   │   │
│   │   └── eval/
│   │       ├── benchmark.py
│   │       ├── metrics.py
│   │       └── dataset/         ← labeled benchmark companies
│   │
│   └── tests/
│
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── app/
│   │   ├── page.tsx             ← landing / run input
│   │   ├── runs/[id]/page.tsx   ← live progress + memo viewer
│   │   └── layout.tsx
│   ├── components/
│   │   ├── RunForm.tsx
│   │   ├── ProgressFeed.tsx
│   │   ├── MemoViewer.tsx
│   │   └── CitationCard.tsx
│   └── lib/
│       └── api.ts
│
├── data/
│   ├── cache/                   ← LLM response cache (gitignored)
│   ├── runs/                    ← persisted run outputs
│   └── eval/                    ← benchmark dataset
│
└── docs/
    ├── architecture.md
    ├── decisions/               ← ADRs
    │   ├── 001-async-not-celery.md
    │   ├── 002-sqlite-not-postgres.md
    │   └── 003-sse-not-websockets.md
    └── interview-prep.md
```

**Why this structure helps the resume:**

- ADR folder signals real engineering practice
- Clear separation of concerns: agents / orchestrator / sources / store / eval
- Eval folder is a strong differentiator from typical student projects

---

## 6. Data Flow Walkthrough

What happens when a user types "Stripe" and clicks Run.

### Step 1 — User Input

- Frontend POSTs `{ company: "Stripe" }` to `/api/runs`
- Backend creates a `Run` record (`status=pending`), returns `run_id`
- Frontend redirects to `/runs/{id}` and opens an SSE connection to `/api/runs/{id}/events`

### Step 2 — Planning

- Backend kicks off async background task
- Planner emits `event: planning_started`
- Planner LLM call decides which agents to run (MVP: always all 4)
- Planner emits `event: agents_dispatched` with the list

### Step 3 — Parallel Agent Execution

All 4 agents run concurrently via `asyncio.gather`. Each agent:

1. Emits `event: agent_started { name }`
2. Fetches data from assigned sources
3. Stores raw data as `Evidence` records (with source URL, fetched_at)
4. Calls LLM to extract structured findings (citations reference evidence IDs)
5. Stores `Finding` records linking back to `Evidence`
6. Emits `event: agent_completed { name, findings_count }`

### Step 4 — Critic Pass

- Critic loads all `Finding` records
- Scores each: confidence (0-1), evidence_quality (0-1), is_supported_by_citation (bool)
- Findings below threshold are flagged
- Emits `event: critic_completed { passed, flagged }`

### Step 5 — Synthesis

- Synthesizer loads approved findings, grouped by section
- Generates memo with structured sections; each claim links to a Finding (which links to Evidence)
- Stores `Memo` record
- Emits `event: memo_ready`

### Step 6 — User Reads Memo

- Frontend renders memo
- Hovering any cited claim shows the source paragraph + URL

**The pattern:** every event is observable, every claim is traceable, every step is testable in isolation. This is the architectural rigor that makes Meridian resume-worthy.

---

## 7. Database Schema

SQLite for MVP. Simple but reveals real thinking.

### 7.1 Tables

**Run**
| Field | Type |
|---|---|
| id | uuid |
| company_name | string |
| status | enum: pending, planning, agents_running, critic_running, synthesizing, complete, failed |
| created_at | timestamp |
| completed_at | timestamp |
| error | string (nullable) |

**Evidence** — raw data fetched from sources
| Field | Type |
|---|---|
| id | uuid |
| run_id | fk → Run |
| source_type | enum: sec, wikipedia, reddit, github, news |
| source_url | string |
| content | text |
| fetched_at | timestamp |
| agent_name | string |

**Finding** — structured claim extracted by an agent
| Field | Type |
|---|---|
| id | uuid |
| run_id | fk → Run |
| agent_name | enum: financial, market, people, customer |
| section | string (e.g. "revenue_growth") |
| claim | text |
| confidence | float 0-1 (agent's self-rating) |
| critic_score | float 0-1 (nullable, set by critic) |
| critic_notes | text (nullable) |
| status | enum: pending_review, approved, rejected |

**EvidenceRef** — join table linking Findings to Evidence
| Field | Type |
|---|---|
| finding_id | fk → Finding |
| evidence_id | fk → Evidence |
| span | optional char offsets within evidence content |

**Memo**
| Field | Type |
|---|---|
| id | uuid |
| run_id | fk → Run |
| content | json (structured sections) |
| generated_at | timestamp |
| model_used | string |

**LLMCacheEntry**
| Field | Type |
|---|---|
| id | sha256(prompt + model) |
| prompt_hash | sha256 |
| model | string |
| prompt | text |
| response | text |
| created_at | timestamp |

### 7.2 Why This Schema Is Good

1. **Provenance is structural.** Findings link to Evidence by design — you cannot have a memo claim without traceability.
2. **Agent isolation.** Each Finding tags its source agent — debug, eval, and iterate per agent.
3. **Critic separation.** Critic scores live on Finding rows; one round-trip, one truth.
4. **Cache as first-class.** Every LLM call is reproducible. Demos are deterministic.

This schema is itself an interview answer. When asked "how do you handle citations?" — point here and say: *"Every claim is a row that joins to evidence rows. There is no claim that exists without a citation by construction."*

---

## 8. Agent Responsibility Matrix

| Agent | Primary Sources | Output Sections | Key Risks |
|---|---|---|---|
| **Financial** | SEC EDGAR (10-K, 10-Q), Yahoo Finance via `yfinance` | Revenue trend, profitability, balance sheet highlights, recent guidance | Hallucinating numbers — must use structured extraction |
| **Market** | Wikipedia, NewsAPI free tier, company website | Market size, competitive landscape, recent industry trends | Generic/vague claims — prompt for specificity |
| **People** | Wikipedia (key people), GitHub (org activity), news mentions | Founders/executives, key hires/departures, organizational signals | Privacy — only public figures, only public info |
| **Customer Sentiment** | Reddit (free API), light review-site scrapes, news | Public sentiment, common complaints, brand perception | Sample bias — must caveat findings |

Build order: **Financial first**, end-to-end, fully working with citations. Then duplicate the pattern for the rest.

---

## 9. Evaluation Framework

The single highest-leverage thing in this project. Most students don't have evals. You will.

### 9.1 Benchmark Dataset

- 20 well-known public companies (Apple, Microsoft, Coinbase, Airbnb, Snowflake, Tesla, etc.)
- For each: 10-15 manually verified ground-truth claims (e.g. "2023 revenue was $X", "HQ in Y", "Top competitor is Z")
- Total: ~250 ground-truth claims

### 9.2 Metrics

| Metric | Definition | Target |
|---|---|---|
| Factual Accuracy | % of overlapping memo claims that match ground truth | >85% |
| Citation Precision | % of citations that actually support their attached claim | >90% |
| Citation Recall | % of significant claims that have a citation | >95% |
| Hallucination Rate | % of memo claims contradicting ground truth or unsourced | <5% |
| Coverage | % of ground-truth facts present in memo | >60% |

### 9.3 Baseline Comparison

Run the same 20 companies through a single Claude/Gemini prompt ("write a diligence memo on X"). Measure the same metrics. Show Meridian beats baseline on accuracy and citation quality.

**A single eval table on the README is worth more than 1000 lines of code.**

---

## 10. Caching Strategy

Three caches; understand each.

| Cache | Location | What | Why |
|---|---|---|---|
| LLM Response | `data/cache/llm/{prompt_hash}.json` | (prompt + model) → response | The big one. Eliminates 90%+ of dev iteration costs. |
| Source Data | `data/cache/sources/{source}/{key}.json` | Raw API/scrape responses | Reddit and SEC are slow; cache aggressively |
| Run | `data/runs/{run_id}/` | Full intermediate outputs | Lets you replay a run instantly for demos |

**Critical rule:** during dev, **always-cache by default**. Add a `--no-cache` flag for the rare times you want fresh data. Most students do the opposite and burn through credits.

---

## 11. Tech Stack & Tooling

| Layer | Choice | Reason |
|---|---|---|
| Backend | Python 3.11 + FastAPI | Async-native, great for SSE, beginner-friendly |
| Frontend | Next.js 14 (App Router) + Tailwind | Fast to build, good defaults |
| Database | SQLite (dev) → optional Postgres (deploy) | Zero setup; portable |
| ORM | SQLModel (Pydantic + SQLAlchemy) | Single source of truth for schemas |
| LLM (dev) | Ollama running `qwen2.5:7b` | Free, local, decent function-calling |
| LLM (demo) | Gemini 2.0 Flash free tier OR Claude Haiku via $5 free credits | Polished output for the recorded demo |
| Streaming | Server-Sent Events | Simpler than WebSockets |
| Validation | Pydantic v2 | Runtime + structural correctness |
| Testing | pytest + pytest-asyncio | Standard |
| Hosting (FE) | Vercel free tier | Native Next.js |
| Hosting (BE) | Railway or Render free tier | Easy Python deploys |
| Source control | Git + GitHub | Public repo for resume |

---

## 12. 14-Day Milestone Roadmap

| Day | Phase | Deliverable |
|---|---|---|
| 1 | 1 | Env set up, repo created, Ollama running with `qwen2.5:7b` |
| 2 | 2 | FastAPI skeleton, health endpoint, logging, SSE proof-of-concept |
| 3 | 3 | LLM client wrapper with disk cache, structured output via Pydantic, retries |
| 4 | 4 | **Financial Agent end-to-end**: SEC + Yahoo, structured findings with citations |
| 5 | 4 | Market Agent + Wikipedia/NewsAPI sources |
| 6 | 4 | People Agent + Customer Sentiment Agent |
| 7 | 5 | Orchestrator: parallel execution, progress events, evidence aggregation |
| 8 | 6 | Critic Agent + scoring + flagging logic |
| 9 | 7 | Synthesizer: structured memo with citations |
| 10 | 8 | Frontend: form, progress feed, memo viewer with citations |
| 11 | 8 | Frontend polish, error states, empty states |
| 12 | 9 | Eval framework + 20-company benchmark + baseline comparison |
| 13 | 10 | Deployment, demo polish, pre-cached demo runs |
| 14 | 11 | README, demo video, resume bullets, LinkedIn post |

**Realistic expectation:** ~85% completion. Plan for 100%, descope from the bottom up if needed.

---

## 13. Risk Register

Sorted by likelihood × impact.

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Local Ollama produces inconsistent JSON | High | High | Use `qwen2.5:7b` (good function-calling), force structured output, validate with Pydantic, retry once |
| Demo is slow during interview | High | High | Pre-cache 3-5 famous companies; demo replays from cache instantly |
| Reddit/SEC APIs rate-limit | Medium | Medium | Aggressive source caching + rate-limit-aware fetchers |
| Synthesizer memo quality is mediocre | High | Medium | Use Gemini Flash for synthesis only; keep local models for agents |
| Scope creep in week 2 | High | High | `FUTURE.md`. Park ideas. Do not implement. |
| Frontend takes longer than expected | Medium | Medium | Use Tailwind + shadcn/ui templates; don't design from scratch |
| Eval framework gets cut | Medium | **Very High** | **Eval is non-negotiable.** Cut a frontend feature first. |
| Citation linking is buggy | Medium | High | Test citations on the first agent before building agent #2 |

---

## 14. Token-Saving Playbook

Beyond caching:

1. **Cache-first development.** Never run an uncached call during normal dev work.
2. **Tier your models.** Local Ollama for cheap tasks (extraction, classification). Gemini Flash free tier for synthesis only.
3. **Trim context.** Don't pass entire 10-K filings to the LLM. Pre-extract relevant sections via regex/heuristics first.
4. **One LLM call per agent for findings.** Not five. Design prompts to extract everything in a single structured call.
5. **Critic batch-scores.** Score the whole batch in one call, not per-finding.
6. **Pre-warm demo cache.** The night before any demo, run all demo companies once. Demos become instant and free.
7. **Streaming is for UX, not for cost.** SSE doesn't reduce LLM cost — it just hides latency.

---

## 15. Architecture Decision Records (ADRs)

Each ADR documents one significant decision. Living entries; updated as understanding grows.

### ADR-001: Use asyncio, not Celery

- **Status:** Accepted
- **Context:** Need parallel agent execution.
- **Decision:** asyncio + `asyncio.gather` in a single FastAPI process.
- **Consequences:** Simpler ops, no extra service. Won't scale beyond ~50 concurrent runs — acceptable for MVP.
- **Alternatives:** Celery+Redis (more moving parts), Temporal (over-engineered for scope).

### ADR-002: Use SQLite, not Postgres for MVP

- **Status:** Accepted
- **Context:** Need persistent storage for runs, evidence, findings, memos.
- **Decision:** SQLite single-file DB.
- **Consequences:** Zero setup. Migrate to Postgres only if deploying with concurrent writers.
- **Alternatives:** Postgres (more setup), DuckDB (analytical, not transactional).

### ADR-003: Use SSE, not WebSockets for streaming

- **Status:** Accepted
- **Context:** Need server → client progress updates.
- **Decision:** Server-Sent Events.
- **Consequences:** Simpler protocol; one-way push fits perfectly.
- **Alternatives:** WebSockets (bidirectional — overkill), polling (worse UX).

### ADR-004: Local Ollama + free Gemini, no paid APIs

- **Status:** Accepted
- **Context:** Build with zero monetary spend.
- **Decision:** `qwen2.5:7b` via Ollama for dev; Gemini 2.0 Flash free tier for final demo synthesis.
- **Consequences:** Slightly lower memo polish during dev; free; positions cost engineering as an interview signal.
- **Alternatives:** Pay-as-you-go OpenAI/Anthropic ($).

---

## 16. Success Criteria

Meridian is a success if, by end of Day 14:

- [ ] Run completes end-to-end on 5+ different public companies
- [ ] Every memo claim has at least one citation linking to source URL
- [ ] Live progress UI streams agent events in real time
- [ ] Eval framework runs over the 20-company benchmark and produces a metrics table
- [ ] Meridian beats single-prompt baseline on at least 3 of 5 metrics
- [ ] README has architecture diagram, eval table, demo video link
- [ ] 60-second demo video plays cleanly with no awkward waits
- [ ] Resume bullet, LinkedIn post, and 3 prepared interview answers are written

If anything is missing, fix that before adding new features.

---

## 17. Resume & Interview Strategy

### 17.1 Resume Bullet Template

> **Meridian — Multi-Agent Due Diligence System** — github.com/you/meridian | demo link
> - Designed and built a 4-agent orchestration system that produces investment-grade diligence memos in 12 minutes (vs. industry-standard 1-2 weeks of analyst work).
> - Implemented evaluation framework on 20-company benchmark; achieved [X]% factual accuracy and [Y] citation precision vs. [Z]% for single-prompt baseline.
> - Designed adversarial critic agent that re-spawns investigations on low-confidence outputs, reducing hallucinated financial claims by [N]%.
> - Stack: Python/FastAPI, Next.js, Ollama + Gemini, pgvector, async orchestration via asyncio.

### 17.2 Three Interview Stories To Prepare

1. **A hard technical decision.** *"I had to choose between embedding the critic inline with each agent or running it as a separate pass. Inline would be faster but coupled critic logic to each agent and prevented batch scoring. I chose a separate pass; it added 30s of latency but enabled batch evaluation, simpler debugging, and the ability to re-run the critic without re-running agents."*
2. **A user/product insight.** *"My first version dumped all 50 findings into the memo. User testing with two finance friends showed they wanted ~10 high-confidence findings, not exhaustive coverage. I added the critic threshold + ranking pipeline. Memos got shorter, scores went up."*
3. **A failure and recovery.** *"Local 7B models produced malformed JSON about 12% of the time. I added Pydantic validation with one retry, and switched the prompt format to tool-call style. Failure rate dropped to under 1%."*

### 17.3 The Architectural Decisions To Foreground

- "I separated the planner from workers so I could test orchestration logic without LLM noise."
- "I used tool-call structured output instead of parsing free text."
- "I built the eval set before adding the second agent."
- "Citations are stored as structured spans, not text quotes."
- "I treat the critic as a separate model call so I can swap it independently."

---

## 18. Comprehension Check

Before moving to Phase 1, you should be able to answer:

1. Why are we using SQLite for MVP and not Postgres? What would change if we needed to swap?
2. What's the difference between an `Evidence` record and a `Finding` record? Why are they separate?
3. Why does the critic agent run *after* all four research agents, not inline with each?
4. Why are we using SSE instead of WebSockets?
5. If you had to cut one item from the 14-day plan, what would it be — and what would you absolutely refuse to cut?

If any feel shaky, revisit the relevant section before continuing.

---

## Document Status

- **Phase 0:** ✅ Complete (this document)
- **Phase 1:** ⏳ Up next — Environment Setup
- **Phases 2-11:** ⏸ Pending

This document is a living artifact. Update it as decisions evolve. Each significant change should be paired with a new ADR in `docs/decisions/`.
