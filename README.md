# Meridian

> Multi-agent due diligence system. Produces structured, citation-backed investment memos on public companies in 8-15 minutes.

🚧 **In active development.** Final README, demo video, and eval results land on Day 14.

---

## What It Does

Type a company name. Meridian spawns four specialized AI agents — Financial, Market, People, and Customer Sentiment — that gather evidence from public sources in parallel. A critic agent evaluates the evidence quality, then a synthesizer produces a structured memo where every claim is cited.

## Why It's Interesting

Most LLM products are single-prompt wrappers. Meridian is an orchestration system:

- **Multi-agent parallel execution** via asyncio
- **Citation grounding** — every memo claim links to a specific source paragraph
- **Adversarial critic agent** — validates findings before synthesis
- **Evaluation framework** — measured against a 20-company benchmark
- **Cost-aware design** — runs entirely on local models during dev

## Architecture

See `docs/PLANNING.md` for the full design document and `docs/decisions/` for ADRs.

## Status

| Phase | Status |
|---|---|
| 0 — Planning | ✅ |
| 1 — Environment Setup | 🟡 In Progress |
| 2 — Backend Skeleton | ⏳ |
| 3 — LLM Wrapper + Cache | ⏳ |
| 4 — Agent System | ⏳ |
| 5 — Orchestrator | ⏳ |
| 6 — Critic Agent | ⏳ |
| 7 — Synthesizer | ⏳ |
| 8 — Frontend | ⏳ |
| 9 — Evaluation | ⏳ |
| 10 — Deployment | ⏳ |
| 11 — Polish | ⏳ |

## Local Development

_Setup instructions land in Phase 1._

## License

MIT (or your preference — finalize on Day 14)
