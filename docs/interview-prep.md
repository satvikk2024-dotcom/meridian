# Meridian — Interview Prep

---

## Resume Bullet

```
Meridian — Multi-Agent Due Diligence System · github.com/satvikkrishna/meridian

- Built a 4-agent AI orchestration system (Financial, Market, Leadership, Sentiment)
  that produces cited investment memos on NSE/BSE-listed companies; cached runs
  complete in under 90 seconds.

- Implemented adversarial critic agent that batch-scores all findings post-hoc;
  financial agent achieved 0% hallucination rate across a 9-company benchmark;
  system average 85% factual accuracy.

- Built evaluation framework with ground-truth coverage metric across 15 companies;
  system achieved 79% ground truth coverage with 11 citations per run on average.

- Stack: Python / FastAPI · Next.js 14 · asyncio · Ollama (qwen2.5:7b) ·
  SSE streaming · SHA-256 disk cache · Pydantic v2
```

---

## Ten-Second Pitch

> "Meridian is a multi-agent system that produces a structured, cited due diligence
> memo on any Indian public company in under 90 seconds — every claim is grounded
> in a verifiable source."

---

## Sixty-Second Pitch

> "Analysts spend the first week of every deal doing mechanical research before any
> real thinking can start. Meridian compresses that. You give it a company name;
> it spawns four specialised AI agents — Financial, Market, Leadership, and Customer
> Sentiment — that pull data from yfinance, Wikipedia, Reddit, and Google News in
> parallel. A critic agent then scores every finding as supported, partially
> supported, or unsupported before a synthesiser writes the memo. The hard part
> isn't the AI — it's the orchestration, the citation grounding, and the evaluation
> framework I built to prove it actually works. On a 9-company benchmark the system
> hit 85% factual accuracy with 11 grounded citations per run. The financial agent
> specifically hit 0% hallucination because all its claims trace directly to
> yfinance numbers."

---

## Three Interview Stories

### 1. A Hard Technical Decision — Critic Architecture

**The question this answers:** "Tell me about a hard design decision you made."

> "I had to decide whether the critic should run inline — checking each agent's
> output as it finished — or as a separate batch pass after all agents completed.
>
> Inline would be faster to implement and slightly lower latency. But it would
> couple critic logic to each agent's code, prevent cross-agent analysis, and make
> re-running the critic impossible without re-running the expensive data-gathering
> agents.
>
> I chose the separate batch pass. It added maybe 20 seconds but meant I could
> write the critic once, run it against all four agents uniformly, and re-execute
> it independently during debugging — critical for the eval loop.
>
> That decision shows up clearly in the benchmark: the critic correctly flags 0%
> for the financial agent because its data is all yfinance numbers, while the
> people agent gets 29% because it's making claims about succession planning that
> no public source can verify."

---

### 2. A Failure and Recovery — Cache Busting in Evals

**The question this answers:** "Tell me about a time something broke and how you fixed it."

> "Mid-project I changed the system prompt on the market agent to make it more
> conservative — 'only state what data directly supports.' The hallucination rate
> jumped from 20% to 26%. I expected it to drop.
>
> It took me a while to figure out why. The issue was that any change to the prompt
> busts the SHA-256 content-addressed LLM cache. So all 9 benchmark companies had
> to make fresh model calls. Fresh calls on a local 7B model have high variance —
> the model was over-hedging and producing vague answers the critic then flagged as
> unsupported.
>
> The fix was to revert the prompt to preserve cache hits, and instead add a
> skip_critic flag so the customer agent's pre-determined short-circuit responses
> were excluded from scoring entirely. The lesson: in eval pipelines, cache
> invalidation isn't just a performance problem — it's a reproducibility problem.
> Any prompt change is a confounding variable."

---

### 3. A Product Insight — Honest Uncertainty Over Coverage

**The question this answers:** "Tell me about a product decision you made."

> "The first version of the memo showed every finding from every agent — about 40
> fields across four agents. It was overwhelming.
>
> I showed it to a couple of people who do financial research and they immediately
> asked 'which parts should I actually read?' That told me the problem wasn't
> information volume — it was trust calibration. They didn't know which claims to
> act on.
>
> I added the critic score as a first-class UI element: sections with flagged
> findings show a warning count, individual fields show an 'unverified' badge. Now
> a user can scan the memo and immediately know which claims are grounded in data
> versus which are the model's inference. That's a more honest product than hiding
> uncertainty, and it's the difference between a toy and something someone might
> actually rely on."

---

## Architectural Points to Foreground

These are the details that separate this from a typical student project.
Bring them up naturally; don't recite them.

- **asyncio.Queue as a message bus** — agents push SSE events into a shared queue;
  the generator pulls and streams them. This is the standard async fan-out / fan-in
  pattern used in real streaming systems.

- **Content-addressed cache** — `SHA-256(prompt)` as the cache key means the same
  query never hits the model twice, evals are reproducible, and dev costs are zero.
  Changing the prompt is a deliberate act with a visible consequence.

- **Pydantic-validated LLM output** — structured output + retry-on-failure means
  malformed JSON doesn't crash the pipeline. Failure rate dropped from ~12% to
  under 1% with one retry + schema injection in the corrective prompt.

- **skip_critic flag** — customer agent short-circuits when fewer than 3 relevant
  Reddit posts are found, returning a pre-determined low-confidence response rather
  than hallucinating. That response is excluded from critic scoring via a flag on
  AgentResult. Shows awareness of when not to use an LLM.

- **Separation of planner and runner** — the planner just returns a list of agents;
  the runner handles concurrency. Testing orchestration logic doesn't require model
  calls.

---

## Questions You Should Be Able to Answer Cold

1. Why asyncio and not Celery or a message queue?
   > Single process, zero infrastructure, easy to reason about. Celery adds Redis,
   > workers, and operational overhead that a solo MVP doesn't need.

2. Why SSE and not WebSockets?
   > Data flows one way — server to browser. SSE is HTTP, works through proxies,
   > reconnects automatically. WebSockets add bidirectional complexity for no gain here.

3. Why SQLite and not Postgres?
   > Zero setup. Single file. WAL mode handles concurrent reads fine. Swapping to
   > Postgres is one connection string change when hosting requires it.

4. Why a separate critic agent instead of asking each agent to self-evaluate?
   > Self-evaluation is unreliable — the same model that generated a claim will tend
   > to validate it. A separate pass with a different prompt framing produces more
   > calibrated scores.

5. What would you change if this needed to handle 100 concurrent users?
   > Move to Postgres with connection pooling, run the LLM calls through a proper
   > job queue (Celery + Redis or similar), and cache at the API gateway layer for
   > repeated queries on the same company.
