"""
Customer Sentiment agent. Analyses retail investor and public sentiment
using Reddit posts from r/IndiaInvestments and r/IndianStockMarket.

"Customer sentiment" here means: how does the investing public perceive
this company? What concerns and themes are retail investors discussing?
"""
import structlog
from pydantic import Field

from app.agents.base import Agent, AgentResult, Citation
from app.llm.schemas import LLMOutputBase, parse_response
from app.sources.reddit import fetch_mentions

logger = structlog.get_logger()

SYSTEM_PROMPT = """You are a sentiment analyst reviewing retail investor discussion about Indian stocks.
You are given Reddit post titles and snippets from investment communities.

Rules:
- Summarise the dominant themes, not individual posts.
- Distinguish between noise (hype/FUD) and substantive concerns.
- Note the volume and recency signals if available.
- Be calibrated — Reddit is noisy; flag low confidence if there are few posts.
"""

_MIN_RELEVANT_POSTS = 3


class SentimentFindings(LLMOutputBase):
    overall_sentiment: str = Field(description="Bullish / Bearish / Mixed / Neutral")
    dominant_themes: list[str] = Field(description="Top 2-3 themes in the discussion")
    key_concerns: list[str] = Field(description="Recurring concerns raised by retail investors")
    positive_signals: list[str] = Field(description="Positive points frequently mentioned")
    noise_warning: str = Field(description="Any signs that discussion is hype/FUD rather than substantive")
    confidence: float = Field(description="0.0-1.0 — low if very few posts found")


def _filter_relevant(company: str, posts: list[dict]) -> list[dict]:
    """Keep only posts that explicitly mention the company by name."""
    name_lower = company.lower()
    # Also match common short names (e.g. "Reliance" for "Reliance Industries")
    short = name_lower.split()[0]
    return [
        p for p in posts
        if name_lower in (p["title"] + p.get("selftext", "")).lower()
        or short in (p["title"] + p.get("selftext", "")).lower()
    ]


def _build_prompt(company: str, posts: list[dict]) -> str:
    lines = [
        f"Analyse retail investor sentiment for {company} based on these Reddit posts.",
        "",
        f"=== REDDIT POSTS ({len(posts)} found) ===",
    ]
    if not posts:
        lines.append("  No relevant posts found.")
    else:
        for i, p in enumerate(posts, 1):
            lines.append(f"\n  [{i}] {p['title']} (score: {p['score']}, comments: {p['num_comments']})")
            if p["selftext"]:
                lines.append(f"      {p['selftext'][:200]}")

    lines += ["", "Produce a structured sentiment analysis using ONLY the posts above."]
    return "\n".join(lines)


class CustomerSentimentAgent(Agent):
    name = "customer"

    async def run(self, company: str, ticker: str) -> AgentResult:
        logger.info("customer_agent_start", company=company, ticker=ticker)

        reddit_data = await fetch_mentions(company)
        all_posts = reddit_data["posts"]
        relevant_posts = _filter_relevant(company, all_posts)

        citations = []
        for post in relevant_posts[:5]:  # cite only relevant posts
            citations.append(Citation(
                source="reddit",
                label=post["title"][:60],
                value=f"score: {post['score']}",
                url=post["url"],
            ))

        # Short-circuit: not enough relevant signal — skip LLM to avoid hallucination
        if len(relevant_posts) < _MIN_RELEVANT_POSTS:
            logger.info(
                "customer_agent_insufficient_data",
                company=company,
                relevant=len(relevant_posts),
                total=len(all_posts),
            )
            return AgentResult(
                agent_name=self.name,
                company=company,
                findings={
                    "overall_sentiment": "Insufficient data",
                    "dominant_themes":   [],
                    "key_concerns":      [],
                    "positive_signals":  [],
                    "noise_warning":     f"Only {len(relevant_posts)} relevant Reddit posts found — too few to assess.",
                    "confidence":        0.1,
                },
                evidence={"reddit": reddit_data},
                citations=citations,
                skip_critic=True,   # pre-determined response, not LLM claims
            )

        # Pass all_posts to prompt so the cache key matches previous runs
        prompt = _build_prompt(company, all_posts)
        try:
            findings = await parse_response(SentimentFindings, prompt, system=SYSTEM_PROMPT)
            logger.info("customer_agent_done", company=company, posts_analysed=len(all_posts))
            return AgentResult(
                agent_name=self.name,
                company=company,
                findings=findings.model_dump(),
                evidence={"reddit": reddit_data},
                citations=citations,
            )
        except Exception as exc:
            logger.error("customer_agent_failed", company=company, error=str(exc))
            return AgentResult(
                agent_name=self.name,
                company=company,
                evidence={"reddit": reddit_data},
                citations=citations,
                error=str(exc),
            )
