"""
Financial agent. Fetches stock fundamentals + company background + recent news,
then asks the LLM to produce structured findings grounded in that evidence.

Flow:
    1. Fetch stock data (yfinance), Wikipedia summary, and news headlines in parallel
    2. Build a prompt from stock + wiki data only (news added as citations, not in prompt)
    3. Call parse_response → FinancialFindings (Pydantic model)
    4. Append news citations with real publish timestamps (enables recency scoring)
    5. Wrap findings + evidence + citations into AgentResult

Why news is not in the LLM prompt:
    - Keeps the prompt cache stable (same yfinance+wiki data = same hash = cache hit)
    - News headlines are supplementary evidence, not primary analysis inputs
    - The Citation.fetched_at field captures article age for recency metrics
"""
import asyncio
import structlog
from pydantic import Field

from app.agents.base import Agent, AgentResult, Citation
from app.llm.schemas import LLMOutputBase, parse_response
from app.sources.bse import fetch_stock_data
from app.sources.news import fetch_news
from app.sources.wikipedia import fetch_summary

logger = structlog.get_logger()

SYSTEM_PROMPT = """You are a senior equity research analyst specialising in Indian public markets.
You are given verified financial data about a company. Your job is to produce a structured analysis.

Rules:
- Base every claim on the data provided. Do not invent numbers.
- Be specific. Use the exact figures given.
- Flag anything that looks concerning (high debt, negative growth, etc.).
- Confidence should reflect how complete the data is (0.0 = no data, 1.0 = very clear picture).
"""


class FinancialFindings(LLMOutputBase):
    """Structured output from the Financial agent."""
    revenue_trend: str = Field(description="Revenue growth trajectory and key driver")
    profitability: str = Field(description="Net income and margin assessment")
    valuation: str = Field(description="P/E and P/B assessment vs sector norms")
    balance_sheet_health: str = Field(description="Debt/equity and cash flow quality")
    key_risks: list[str] = Field(description="Top 2-3 financial risks identified")
    key_strengths: list[str] = Field(description="Top 2-3 financial strengths")
    analyst_view: str = Field(description="Summary of analyst consensus if available")
    confidence: float = Field(description="0.0-1.0: how complete is the financial picture")


def _build_prompt(company: str, stock: dict, wiki: dict) -> str:
    lines = [
        f"Analyse the financial health of {company} (ticker: {stock['ticker']}).",
        "",
        "=== STOCK FUNDAMENTALS ===",
    ]
    for k, v in stock.items():
        if k not in ("ticker", "company_name", "business_summary"):
            lines.append(f"  {k}: {v}")

    if wiki.get("found"):
        lines += [
            "",
            "=== COMPANY BACKGROUND (Wikipedia) ===",
            wiki["summary"][:800],  # ~200 tokens — enough context without bloat
        ]

    lines += [
        "",
        "Produce a structured analysis using ONLY the data above.",
    ]
    return "\n".join(lines)


class FinancialAgent(Agent):
    name = "financial"

    async def run(self, company: str, ticker: str) -> AgentResult:
        logger.info("financial_agent_start", company=company, ticker=ticker)

        # Fetch all three sources in parallel
        stock_data, wiki_data, news_items = await asyncio.gather(
            fetch_stock_data(ticker),
            fetch_summary(company),
            fetch_news(company),
        )

        # Build citations from yfinance + wikipedia
        citations = [
            Citation(source="yfinance", label="Market Cap", value=stock_data["market_cap"],
                     url=f"https://finance.yahoo.com/quote/{ticker}"),
            Citation(source="yfinance", label="Revenue (TTM)", value=stock_data["revenue_ttm"],
                     url=f"https://finance.yahoo.com/quote/{ticker}/financials"),
            Citation(source="yfinance", label="Net Income (TTM)", value=stock_data["net_income_ttm"],
                     url=f"https://finance.yahoo.com/quote/{ticker}/financials"),
            Citation(source="yfinance", label="P/E Ratio", value=stock_data["pe_ratio"],
                     url=f"https://finance.yahoo.com/quote/{ticker}"),
            Citation(source="yfinance", label="Debt/Equity", value=stock_data["debt_to_equity"],
                     url=f"https://finance.yahoo.com/quote/{ticker}/balance-sheet"),
        ]
        if wiki_data.get("found"):
            citations.append(Citation(
                source="wikipedia", label="Company Overview",
                value=wiki_data["title"], url=wiki_data["url"],
            ))

        # Append news citations with real publish timestamps (no LLM call)
        for item in news_items[:5]:
            citations.append(Citation(
                source="news",
                label=item["title"][:70],
                value=item["source"],
                url=item["url"],
                fetched_at=item["published_at"],
            ))

        # LLM prompt uses only yfinance + wiki — preserves cache hash
        prompt = _build_prompt(company, stock_data, wiki_data)
        try:
            findings = await parse_response(
                FinancialFindings,
                prompt,
                system=SYSTEM_PROMPT,
            )
            logger.info("financial_agent_done", company=company, news_count=len(news_items))
            return AgentResult(
                agent_name=self.name,
                company=company,
                findings=findings.model_dump(),
                evidence={"stock": stock_data, "wikipedia": wiki_data},
                citations=citations,
            )
        except Exception as exc:
            logger.error("financial_agent_failed", company=company, error=str(exc))
            return AgentResult(
                agent_name=self.name,
                company=company,
                evidence={"stock": stock_data, "wikipedia": wiki_data},
                citations=citations,
                error=str(exc),
            )
