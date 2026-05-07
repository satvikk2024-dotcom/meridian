# ADR-004: Use local Ollama (and free Gemini for demos), not paid LLM APIs

## Status
Accepted — 2026-05

## Context

Meridian uses LLMs for: agent extraction, critic scoring, and memo synthesis.
LLM API costs are the dominant cost in any agentic system. Options:

- **Pay-as-you-go (Anthropic, OpenAI, Cohere)** — Best quality. Real cost: $2-5 per Meridian run.
  Dev iteration could easily cost $100-300.
- **Local Ollama** — Free. Runs `qwen2.5:7b`, `llama3.1:8b`, etc., on your machine.
  Lower quality but adequate for most agent tasks.
- **Free tiers (Gemini, Groq, Cerebras, OpenRouter)** — Mid-quality, rate-limited, no cost.

## Decision

- **Default LLM during dev:** Ollama running `qwen2.5:7b`.
- **Final-demo LLM (synthesizer only):** Gemini 2.0 Flash free tier.
- **Backup option:** Anthropic's $5 free credit allotment with Claude Haiku 4.5 for high-quality
  demo runs.
- **Never:** Pay-as-you-go without explicit approval.

## Reasoning

- The architectural value of Meridian (orchestration, eval, citations) is independent of model
  quality. Lower-quality models force the system design to actually carry the weight.
- Local Ollama eliminates ~95% of dev API spend; it's also a stronger interview signal —
  cost-engineering is a real production AI skill.
- Gemini Flash free tier is sufficient for the polished synthesis step on demo runs.

## Consequences

**Positive:**
- Zero monetary spend during development.
- Reproducible runs (cache + local model = deterministic given the same prompt).
- "I built this on free-tier inference" is a positive interview signal.

**Negative:**
- `qwen2.5:7b` produces less polished prose than Claude Sonnet — synthesis quality varies.
- Local inference is slower per call (1-3s) than hosted APIs (0.5-1s) — we hide this with
  streaming UI and batching.
- Smaller models occasionally produce malformed JSON — mitigated by Pydantic validation
  and one retry.

## Caching Implications

The cache layer is built **before the first agent**, not after. Every LLM call goes through:

```
client.generate(prompt, model)
  ↓
hash = sha256(prompt + model)
  ↓
if cached(hash): return cached
  ↓
otherwise: call LLM, store response, return
```

This means re-running the same Meridian run on the same company is **free**.

## Migration Path

If quality becomes a hard blocker:

1. Swap synthesizer to Gemini Flash free tier (already planned for final demos).
2. Use Anthropic free credits for high-stakes runs.
3. Eventually allow user to bring their own API key.

## Interview Talking Point

> "I built it on free-tier inference because I wanted to prove the architecture works regardless
> of model. The orchestrator and critic care about *what* gets called, not *which* model. When
> I switched the synthesizer to Gemini Flash for the final demo, quality went up but the system
> worked identically — which validated the design. Cost engineering is part of the product."
