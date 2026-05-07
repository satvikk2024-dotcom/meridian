# FUTURE — Parked Ideas

> Anything that is NOT in the locked MVP scope goes here.
> Do not implement these without explicit re-scoping.
>
> The MVP scope (per `docs/PLANNING.md`):
> - 4 agents (Financial, Market, People, Customer Sentiment)
> - 1 memo template
> - SSE streaming progress UI
> - Citation grounding
> - Critic agent (post-hoc, batch scoring)
> - Evaluation framework (20-company benchmark)
> - Polished demo flow

---

## Post-MVP Ideas

_Nothing parked yet. When ideas come up that don't fit the MVP, add them here with a one-line
rationale for why they're "later, not now."_

### Template

```
- [Idea name]
  - Why later: [reason]
  - When relevant: [signal that says "now is the time"]
  - Estimated effort: [small / medium / large]
```

---

## Examples (Don't Implement)

- **User accounts and auth**
  - Why later: not needed for a single-user demo; adds Clerk/Auth.js setup
  - When relevant: ever sharing publicly with multiple distinct users
  - Estimated effort: small (with Clerk), medium (custom)

- **PDF / DOCX export**
  - Why later: web view is sufficient for the demo; PDF gen is fiddly
  - When relevant: once we have actual users requesting it
  - Estimated effort: small (using `weasyprint` or similar)

- **Industry-specific memo templates**
  - Why later: one good template proves the architecture; multiple split focus
  - When relevant: actual user demand from a specific vertical
  - Estimated effort: medium (template engine refactor)

- **Continuous monitoring (re-runs on new data)**
  - Why later: requires scheduling, change detection, deduplication, notification
  - When relevant: paying users who follow companies long-term
  - Estimated effort: large

- **Real-time / collaborative memos**
  - Why later: massive scope, needs CRDTs or similar; not a wedge feature
  - When relevant: post-product-market-fit
  - Estimated effort: large

- **Custom data source integrations (Crunchbase, PitchBook, AlphaSense)**
  - Why later: paid APIs; conflicts with zero-budget constraint
  - When relevant: with funding or for paid customer
  - Estimated effort: medium per integration

- **Multi-LLM provider abstraction**
  - Why later: We already abstract via `llm/client.py`. More providers = more configuration UI.
  - When relevant: users want to bring their own keys
  - Estimated effort: small per provider

- **Mobile UI**
  - Why later: desktop UI is the demo target; mobile is rarely used for diligence
  - When relevant: never, probably
  - Estimated effort: medium
