# Meridian Benchmark Report
_Generated: 2026-05-09 19:00 | Companies: 9_

## Summary

| Company | HAL% | Citations | Completeness | GT Coverage |
|---------|------|-----------|--------------|-------------|
| Reliance Industries       | 6%    | 11        | 78%          | 67% |
| TCS                       | 17%   | 11        | 78%          | 79% |
| HDFC Bank                 | 17%   | 11        | 78%          | 79% |
| Infosys                   | 12%   | 11        | 78%          | 64% |
| ITC                       | 11%   | 11        | 78%          | 86% |
| Wipro                     | 11%   | 11        | 78%          | 86% |
| ICICI Bank                | 17%   | 11        | 78%          | 86% |
| Bharti Airtel             | 22%   | 11        | 78%          | 79% |
| HCL Technologies          | 22%   | 11        | 87%          | 86% |
| **Average**                | **15%** | 11.0      | **79%**  | 79% |

## Per-Agent Hallucination Rates

| Agent | Avg HAL% | Worst | Best |
|-------|----------|-------|------|
| financial    | 0%        | 0%     | 0% |
| market       | 20%       | 50%    | 0% |
| people       | 29%       | 60%    | 0% |

### By Company

| Company | financia | market | people |
|---------|----------|--------|--------|
| Reliance Industries       | 0% | 0% | 20% |
| TCS                       | 0% | 50% | 0% |
| HDFC Bank                 | 0% | 33% | 20% |
| Infosys                   | 0% | 0% | 40% |
| ITC                       | 0% | 0% | 40% |
| Wipro                     | 0% | 17% | 20% |
| ICICI Bank                | 0% | 0% | 60% |
| Bharti Airtel             | 0% | 50% | 20% |
| HCL Technologies          | 0% | 33% | 40% |

## Citation Source Breakdown

| Source | Total Citations | Share |
|--------|-----------------|-------|
| yfinance     | 81              | 82% |
| wikipedia    | 18              | 18% |

## Top Problematic Findings

_Findings flagged as unsupported by the critic across all companies:_

### 1. `key_risks` — people agent — Reliance Industries
> ['Founder-led structure poses a key-person risk', 'Limited details on succession planning']

### 2. `dividend_assessment` — market agent — TCS
> The dividend yield is not accurate as it cannot be over 100%. Assuming a realistic yield of 5.18%, which may attract income investors, but does not significantly enhance total returns compared to growth potential.

### 3. `key_risks` — market agent — TCS
> ['Economic slowdown in key markets could impact demand for IT services.']

### 4. `key_opportunities` — market agent — TCS
> ['Growing global digital transformation trends present substantial long-term growth opportunities.']

### 5. `key_risks` — market agent — HDFC Bank
> ['Interest rate risks due to potential changes in monetary policy', 'Credit risk given the macroeconomic conditions and regulatory environment']

### 6. `key_opportunities` — market agent — HDFC Bank
> ['Continued growth in retail lending and wealth management services', 'Expansion opportunities through organic growth and M&A']

### 7. `key_risks` — people agent — HDFC Bank
> ['No visible succession plan details', 'Market capitalization driven by financial performance which could introduce external risk factors']

### 8. `leadership_overview` — people agent — Infosys
> The leadership team of Infosys consists of a mix of experienced executives including the co-founder and chairman, multiple executive vice presidents, chief financial officer, chief human resources officer, and other key executives in marketing and legal roles.

### 9. `key_risks` — people agent — Infosys
> ['Founder-led structure poses concentration risk', 'Potential for key-person dependency on Mr. Nilekani', 'Lack of detailed information on succession plans']

### 10. `key_person_risk` — people agent — ITC
> Low to Moderate
