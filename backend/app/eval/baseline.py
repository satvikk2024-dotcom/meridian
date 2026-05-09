"""
Baseline comparison: one LLM call, no tools, no agents.

This is the "naive" approach Meridian is measured against.
The same critic and metrics run on baseline output, making the comparison fair.

Why this is a strong baseline:
- Uses the same model (qwen2.5:7b)
- Asks for the same information
- Only difference: no real data injected, no parallel agents, no citations

Expected results:
- High hallucination_rate (critic flags claims with no cited evidence)
- citation_count = 0 (no tools called)
- Lower finding_completeness (LLM hallucinates or skips fields)
"""
import dataclasses

from app.agents.base import AgentResult
from app.agents.critic import run_critic
from app.eval.metrics import compute_all
from app.llm.client import complete

_SYSTEM = (
    "You are a financial analyst. Provide a concise due diligence report on the company given. "
    "Cover: revenue trend, profitability, market valuation, leadership, customer sentiment, "
    "key risks, and key strengths. Be specific where possible."
)

_PROMPT_TEMPLATE = (
    "Company: {company}\n"
    "Ticker: {ticker}\n\n"
    "Provide a structured due diligence analysis covering all the sections in your instructions."
)


async def run_baseline(company: str, ticker: str) -> dict:
    """
    Run a single LLM call with no tools and compute the same metrics.

    Returns a metrics dict comparable to benchmark.run_one().
    """
    prompt = _PROMPT_TEMPLATE.format(company=company, ticker=ticker)
    raw_text = await complete(prompt, system=_SYSTEM, json_mode=False)

    # Package as a single AgentResult so the critic can score it.
    # evidence must be a dict-of-dicts to match critic.py expectations.
    # No citations — the LLM had no real data sources.
    fake_result = AgentResult(
        agent_name="baseline",
        company=company,
        findings={
            "revenue_trend":        _extract_section(raw_text, "revenue") or raw_text[:200],
            "profitability":        _extract_section(raw_text, "profit"),
            "valuation":            _extract_section(raw_text, "valuat"),
            "balance_sheet_health": _extract_section(raw_text, "balance"),
            "key_risks":            _extract_section(raw_text, "risk"),
            "key_strengths":        _extract_section(raw_text, "strength"),
            "analyst_view":         _extract_section(raw_text, "analyst"),
        },
        evidence={"llm_response": {"full_text": raw_text[:500]}},
        citations=[],
        error=None,
    )

    critic_result = await run_critic([fake_result])
    metrics = compute_all([fake_result], critic_result)

    return {
        "company":  company,
        "ticker":   ticker,
        "mode":     "baseline",
        "raw_chars": len(raw_text),
        **metrics,
    }


def _extract_section(text: str, keyword: str) -> str:
    """
    Pull ~200 chars around the first occurrence of a keyword.
    Used to give the critic something to score per field.
    """
    lower = text.lower()
    idx = lower.find(keyword)
    if idx == -1:
        return ""
    start = max(0, idx - 20)
    return text[start : start + 200].strip()
