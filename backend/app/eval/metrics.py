"""
Evaluation metrics for Meridian benchmark runs.

Three metrics, each answerable in one number:
  - hallucination_rate:     % of findings the critic flagged as unsupported
  - citation_count:         deduplicated sources the agents collected
  - finding_completeness:   % of expected fields that are non-empty
"""
from app.agents.base import AgentResult
from app.agents.critic import CriticResult

# Canonical fields per agent (excluding 'confidence' — it's meta, not a finding)
EXPECTED_FIELDS: dict[str, list[str]] = {
    "financial": [
        "revenue_trend", "profitability", "valuation",
        "balance_sheet_health", "key_risks", "key_strengths", "analyst_view",
    ],
    "market": [
        "price_momentum", "valuation_assessment", "sector_position",
        "dividend_assessment", "key_risks", "key_opportunities",
    ],
    "people": [
        "leadership_overview", "key_person_risk",
        "founder_presence", "succession_note", "key_risks",
    ],
    "customer": [
        "overall_sentiment", "dominant_themes",
        "key_concerns", "positive_signals", "noise_warning",
    ],
}

TOTAL_EXPECTED = sum(len(v) for v in EXPECTED_FIELDS.values())  # 23


def hallucination_rate(critic: CriticResult) -> float:
    """Fraction of findings flagged as unsupported by the critic."""
    return critic.hallucination_rate


def citation_count(results: list[AgentResult]) -> int:
    """Number of unique source citations across all agent results."""
    seen: set[str] = set()
    count = 0
    for r in results:
        for c in r.citations:
            key = f"{c.source}:{c.label}"
            if key not in seen:
                seen.add(key)
                count += 1
    return count


def finding_completeness(results: list[AgentResult]) -> float:
    """
    Fraction of expected fields that are populated with non-empty values.

    A field is 'populated' if it is not None, not '', and not an empty list.
    """
    found = 0
    for r in results:
        for field in EXPECTED_FIELDS.get(r.agent_name, []):
            val = r.findings.get(field)
            if val is not None and val != "" and val != []:
                found += 1
    return found / TOTAL_EXPECTED if TOTAL_EXPECTED > 0 else 0.0


def compute_all(
    results: list[AgentResult],
    critic: CriticResult,
) -> dict[str, float | int]:
    """Compute all three metrics and return as a flat dict."""
    return {
        "hallucination_rate": round(hallucination_rate(critic), 3),
        "citation_count":     citation_count(results),
        "finding_completeness": round(finding_completeness(results), 3),
    }
