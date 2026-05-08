# ADR-005: Target Indian Public Markets (NSE/BSE), Not US (SEC)

- **Status:** Accepted
- **Context:** Meridian was originally scoped for US public companies using SEC EDGAR as the primary filing source. The builder is based in India and targets Indian recruiters and companies where an India-focused project has higher contextual resonance.
- **Decision:** Target NSE/BSE-listed Indian public companies. Replace SEC EDGAR with BSE India filing API + Screener.in for financial data. Use yfinance with `.NS`/`.BO` ticker suffixes (already supports Indian exchanges). Update eval benchmark to 20 Indian companies.
- **Consequences:**
  - Resume signal improves: most AI projects target US data; this stands out.
  - yfinance works identically — no code change, just ticker format (`RELIANCE.NS` not `RELIANCE`).
  - BSE has a public filing API (api.bseindia.com) comparable in coverage to SEC EDGAR.
  - Screener.in aggregates Indian financials cleanly and is freely scrapeable.
  - Reddit sources shift to r/IndiaInvestments, r/DalalStreetTalks, r/IndianStockMarket.
  - NewsAPI supports Indian outlets (Economic Times, Mint, Business Standard, Hindustan Times).
  - Architecture, streaming, agent design, critic, synthesizer — all unchanged.
- **Alternatives considered:** Keep US scope (lower differentiation for Indian builder). Support both markets (scope creep — FUTURE.md candidate).
