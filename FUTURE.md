# Future Ideas

Ideas worth building once the core is stable and deployed.

---

- **Deeper customer sentiment sources** — expand beyond Reddit to Twitter/X, stocktwits, earnings call transcripts. Eval first to confirm Reddit is actually the bottleneck.

- **Temporal relevance scoring** — weight findings by recency. Useful when a company has had a major event (earnings miss, leadership change) in the last 30 days.

- **PDF / DOCX export** — web view covers the demo; export matters once real users want to share memos offline. `weasyprint` or `python-docx` would work.

- **Industry-specific memo templates** — one template proves the architecture. Multiple templates (fintech, pharma, FMCG) become relevant once there's demand from a specific vertical.

- **Deeper leadership research** — LinkedIn public data, earnings call speaker analysis, tenure patterns. Currently limited by what Wikipedia and yfinance expose.

- **Multi-user support + auth** — Clerk.js for auth, Postgres for multi-tenant runs. Irrelevant until there are multiple distinct users.

- **Continuous monitoring** — re-run on a schedule and surface diffs when findings change. Requires change detection, deduplication, notification layer. Post-PMF work.

- **Bring-your-own API key** — let users swap in their own Gemini / OpenAI key. The LLM client already abstracts provider; this is mostly configuration UI.

- **Global stock support** — expand beyond NSE/BSE to NYSE/NASDAQ/LSE. The main blocker is the people and sentiment agents, which assume Indian sources (Reddit India subs, Wikipedia coverage of Indian companies).
