"""
Memo section definitions.

Each section maps to one agent's findings plus a template string.
Keeping templates here (separate from assembly logic) means you can
change the memo format without touching memo.py.
"""
from dataclasses import dataclass


@dataclass
class Section:
    title: str          # Markdown heading text
    agent_name: str     # Which AgentResult feeds this section
    fields: list[str]   # Which finding keys to include, in order


SECTIONS: list[Section] = [
    Section(
        title="Financial Health",
        agent_name="financial",
        fields=["revenue_trend", "profitability", "valuation",
                "balance_sheet_health", "key_strengths", "key_risks"],
    ),
    Section(
        title="Market Position",
        agent_name="market",
        fields=["sector_position", "price_momentum", "valuation_assessment",
                "dividend_assessment", "key_opportunities", "key_risks"],
    ),
    Section(
        title="Leadership & Governance",
        agent_name="people",
        fields=["leadership_overview", "founder_presence",
                "key_person_risk", "succession_note", "key_risks"],
    ),
    Section(
        title="Customer & Public Sentiment",
        agent_name="customer",
        fields=["overall_sentiment", "dominant_themes",
                "key_concerns", "positive_signals", "noise_warning"],
    ),
]

# Labels shown in the memo for each finding key
FIELD_LABELS: dict[str, str] = {
    "revenue_trend":        "Revenue Trend",
    "profitability":        "Profitability",
    "valuation":            "Valuation",
    "balance_sheet_health": "Balance Sheet",
    "key_strengths":        "Strengths",
    "key_risks":            "Risks",
    "sector_position":      "Sector Position",
    "price_momentum":       "Price Momentum",
    "valuation_assessment": "Valuation Assessment",
    "dividend_assessment":  "Dividend",
    "key_opportunities":    "Opportunities",
    "leadership_overview":  "Leadership",
    "founder_presence":     "Founder Presence",
    "key_person_risk":      "Key-Person Risk",
    "succession_note":      "Succession",
    "overall_sentiment":    "Overall Sentiment",
    "dominant_themes":      "Dominant Themes",
    "key_concerns":         "Concerns",
    "positive_signals":     "Positive Signals",
    "noise_warning":        "Noise Warning",
}
