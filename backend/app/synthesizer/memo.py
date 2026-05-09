"""
Synthesizer: assembles a markdown due diligence memo from agent results.

Flow:
    1. Build an index of agent results by name
    2. Build an index of critic scores (which findings are flagged)
    3. Write each section using the templates
    4. Append a Risk Summary (aggregated risks across all agents)
    5. Append a Citations section
    6. Return the full markdown string
"""
from datetime import date

import structlog

from app.agents.base import AgentResult, Citation
from app.agents.critic import AgentCriticOutput, CriticResult
from app.synthesizer.templates import FIELD_LABELS, SECTIONS

logger = structlog.get_logger()


def _fmt_value(val) -> str:
    """Format a finding value as a readable markdown string."""
    if isinstance(val, list):
        if not val:
            return "_None identified._"
        return "\n" + "\n".join(f"- {item}" for item in val)
    return str(val)


def _flag_marker(finding_key: str, unsupported: set[str]) -> str:
    """Return a warning marker if this finding was flagged by the critic."""
    if finding_key in unsupported:
        return " ⚠️ _critic: limited evidence_"
    return ""


def _build_section(
    section_title: str,
    agent_name: str,
    fields: list[str],
    results_by_agent: dict[str, AgentResult],
    unsupported_by_agent: dict[str, set[str]],
) -> str:
    result = results_by_agent.get(agent_name)
    if result is None or result.error:
        error_msg = result.error if result else "agent did not run"
        return f"## {section_title}\n\n_Data unavailable: {error_msg}_\n\n"

    lines = [f"## {section_title}\n"]
    unsupported = unsupported_by_agent.get(agent_name, set())

    for key in fields:
        val = result.findings.get(key)
        if val is None:
            continue
        label = FIELD_LABELS.get(key, key.replace("_", " ").title())
        flag = _flag_marker(key, unsupported)
        lines.append(f"**{label}**{flag}  ")
        lines.append(_fmt_value(val))
        lines.append("")

    return "\n".join(lines) + "\n"


def _build_executive_summary(
    company: str,
    ticker: str,
    results_by_agent: dict[str, AgentResult],
    critic: CriticResult,
) -> str:
    financial = results_by_agent.get("financial")
    market = results_by_agent.get("market")
    sentiment = results_by_agent.get("customer")

    lines = ["## Executive Summary\n"]

    # Pull the most important one-liners from each agent
    if financial and not financial.error:
        rev = financial.findings.get("revenue_trend", "")
        if rev:
            lines.append(f"- **Financials:** {rev}")
        prof = financial.findings.get("profitability", "")
        if prof:
            lines.append(f"- **Profitability:** {prof}")

    if market and not market.error:
        pos = market.findings.get("sector_position", "")
        if pos:
            lines.append(f"- **Market:** {pos}")

    if sentiment and not sentiment.error:
        sent = sentiment.findings.get("overall_sentiment", "")
        themes = sentiment.findings.get("dominant_themes", [])
        if sent:
            theme_str = (", ".join(themes[:2]) + ".") if themes else ""
            lines.append(f"- **Sentiment:** {sent}. {theme_str}")

    # Critic summary
    rate_pct = round(critic.hallucination_rate * 100)
    lines.append(
        f"\n_Critic review: {rate_pct}% of findings flagged as weakly evidenced. "
        f"Flagged agents: {', '.join(critic.flagged_agents) or 'none'}._"
    )

    return "\n".join(lines) + "\n\n"


def _build_risk_summary(
    results_by_agent: dict[str, AgentResult],
    unsupported_by_agent: dict[str, set[str]],
) -> str:
    lines = ["## Risk Summary\n", "### Identified Risks\n"]

    for agent_name, result in results_by_agent.items():
        if result.error or not result.findings:
            continue
        risks = result.findings.get("key_risks", [])
        if risks:
            lines.append(f"**From {agent_name} analysis:**")
            for r in risks:
                lines.append(f"- {r}")
            lines.append("")

    # Critic flags
    all_flagged = [
        (agent, key)
        for agent, keys in unsupported_by_agent.items()
        for key in keys
    ]
    if all_flagged:
        lines.append("### Critic Flags (weakly evidenced)\n")
        for agent, key in all_flagged:
            label = FIELD_LABELS.get(key, key)
            lines.append(f"- **{agent}** → {label}")

    return "\n".join(lines) + "\n\n"


def _build_citations(results_by_agent: dict[str, AgentResult]) -> str:
    lines = ["## Citations\n"]
    seen: set[str] = set()
    idx = 1

    for result in results_by_agent.values():
        for c in result.citations:
            dedup_key = f"{c.source}:{c.label}"
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            url_part = f" — [{c.url}]({c.url})" if c.url else ""
            lines.append(f"{idx}. **[{c.source}]** {c.label}: {c.value}{url_part}")
            idx += 1

    return "\n".join(lines) + "\n"


def build_memo(
    company: str,
    ticker: str,
    results: list[AgentResult],
    critic: CriticResult,
) -> str:
    """
    Assemble a full markdown due diligence memo.

    Args:
        company: Human-readable name, e.g. "Reliance Industries"
        ticker:  Exchange ticker, e.g. "RELIANCE.NS"
        results: All agent results from the run
        critic:  Critic scoring of those results
    """
    logger.info("synthesizer_start", company=company, agent_count=len(results))

    # Build lookup dicts for O(1) access
    results_by_agent = {r.agent_name: r for r in results}
    unsupported_by_agent: dict[str, set[str]] = {
        s.agent: set(s.unsupported) for s in critic.scores
    }

    parts: list[str] = []

    # Header
    today = date.today().strftime("%d %B %Y")
    parts.append(f"# Due Diligence Report: {company} ({ticker})\n")
    parts.append(f"_Generated by Meridian · {today}_\n\n---\n\n")

    # Executive summary
    parts.append(_build_executive_summary(company, ticker, results_by_agent, critic))
    parts.append("---\n\n")

    # One section per agent
    for section in SECTIONS:
        parts.append(_build_section(
            section.title, section.agent_name, section.fields,
            results_by_agent, unsupported_by_agent,
        ))
        parts.append("---\n\n")

    # Risk summary and citations
    parts.append(_build_risk_summary(results_by_agent, unsupported_by_agent))
    parts.append("---\n\n")
    parts.append(_build_citations(results_by_agent))

    memo = "".join(parts)
    logger.info("synthesizer_done", company=company, chars=len(memo))
    return memo
