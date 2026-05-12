"""
Evaluation metrics for Meridian benchmark runs.

Core metrics (original):
  hallucination_rate      — % of findings the critic flagged as unsupported
  citation_count          — unique sources the agents collected
  finding_completeness    — % of expected fields that are non-empty

Extended metrics (Phase 9.5 M1):
  per_agent_hallucination — hallucination rate broken down by agent
  source_citation_breakdown — citation counts by source type
  worst_findings          — top N unsupported findings with full context
  ground_truth_coverage   — fraction of known facts the system mentioned
"""
from app.agents.base import AgentResult
from app.agents.critic import CriticResult

# Canonical fields per agent (excluding 'confidence' — meta, not a finding)
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


# ---------------------------------------------------------------------------
# Original metrics
# ---------------------------------------------------------------------------

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
    """Fraction of expected fields populated with non-empty values."""
    found = 0
    for r in results:
        for f in EXPECTED_FIELDS.get(r.agent_name, []):
            val = r.findings.get(f)
            if val is not None and val != "" and val != []:
                found += 1
    return found / TOTAL_EXPECTED if TOTAL_EXPECTED > 0 else 0.0


# ---------------------------------------------------------------------------
# Extended metrics (Phase 9.5 M1)
# ---------------------------------------------------------------------------

def per_agent_hallucination(critic: CriticResult) -> dict[str, float]:
    """Hallucination rate broken down by agent name."""
    result: dict[str, float] = {}
    for score in critic.scores:
        total = (
            len(score.supported)
            + len(score.partially_supported)
            + len(score.unsupported)
        )
        rate = len(score.unsupported) / total if total > 0 else 0.0
        result[score.agent] = round(rate, 3)
    return result


def source_citation_breakdown(results: list[AgentResult]) -> dict[str, int]:
    """Count of unique citations by source type (yfinance, wikipedia, reddit, …)."""
    counts: dict[str, int] = {}
    seen: set[str] = set()
    for r in results:
        for c in r.citations:
            key = f"{c.source}:{c.label}"
            if key not in seen:
                seen.add(key)
                counts[c.source] = counts.get(c.source, 0) + 1
    return counts


def worst_findings(
    results: list[AgentResult],
    critic: CriticResult,
    n: int = 5,
) -> list[dict]:
    """
    Return the N findings flagged as unsupported by the critic, with full context.
    Sorted by agent to make the pattern visible across repeated runs.
    """
    by_agent = {s.agent: s for s in critic.scores}
    bad: list[dict] = []
    for r in results:
        score = by_agent.get(r.agent_name)
        if not score:
            continue
        for key in score.unsupported:
            val = r.findings.get(key, "")
            bad.append({
                "agent":         r.agent_name,
                "finding_key":   key,
                "finding_value": str(val)[:400],
                "company":       r.company,
            })
    # Stable sort: group by agent so the report is easier to read
    bad.sort(key=lambda x: x["agent"])
    return bad[:n]


def ground_truth_coverage(
    results: list[AgentResult],
    claims: list[dict],
) -> float:
    """
    Fraction of verified ground-truth claims mentioned in any agent's findings.

    Uses keyword matching: a claim is 'covered' if any meaningful word from
    its text appears in the combined findings text. Rough but fast.
    """
    if not claims:
        return 1.0
    all_text = " ".join(
        str(v).lower()
        for r in results
        for v in r.findings.values()
    )
    found = sum(1 for c in claims if _claim_mentioned(c["claim"], all_text))
    return round(found / len(claims), 3)


def _claim_mentioned(claim: str, text: str) -> bool:
    """True if any significant word (>4 chars) from claim appears in text."""
    words = [w.lower().strip(".,;:") for w in claim.split() if len(w) > 4]
    if not words:
        return False
    return any(w in text for w in words[:6])


# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------

def compute_all(
    results: list[AgentResult],
    critic: CriticResult,
    ground_truth_claims: list[dict] | None = None,
) -> dict:
    """Compute all metrics and return as a flat dict."""
    metrics: dict = {
        "hallucination_rate":   round(hallucination_rate(critic), 3),
        "citation_count":       citation_count(results),
        "finding_completeness": round(finding_completeness(results), 3),
        "per_agent_hal":        per_agent_hallucination(critic),
        "source_breakdown":     source_citation_breakdown(results),
    }
    if ground_truth_claims is not None:
        metrics["ground_truth_coverage"] = ground_truth_coverage(
            results, ground_truth_claims
        )
    return metrics
