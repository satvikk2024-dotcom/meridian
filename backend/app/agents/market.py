"""
Market agent. Analyses sector positioning, price momentum, and relative
valuation using the same yfinance data the Financial agent already fetched.

Why a separate agent?
- Separation of concerns: Financial = balance sheet health, Market = positioning.
- In the orchestrator, both run in parallel. Mixing them would create a single
  bottleneck and a prompt too long for the model to reason well about.
"""
import structlog
from pydantic import Field

from app.agents.base import Agent, AgentResult, Citation
from app.llm.schemas import LLMOutputBase, parse_response
from app.sources.bse import fetch_stock_data

logger = structlog.get_logger()

SYSTEM_PROMPT = """You are a market analyst specialising in Indian equities.
You receive verified price and valuation data. Produce a concise market positioning analysis.

Rules:
- Focus on price action, sector trends, and competitive position.
- Do not invent peer companies — only reason about what the data shows.
- Be specific about what the valuation multiples imply.
"""


def _sanitize_dividend_yield(raw: object) -> str:
    """Return the yield as a clean string, or 'N/A' if it looks like bad data."""
    if raw in (None, "N/A", ""):
        return "N/A"
    try:
        val = float(str(raw).replace("%", "").strip())
        if val > 0.20:  # yfinance returns a fraction (e.g. 0.018 = 1.8%)
            return "N/A (data error)"
        return f"{val * 100:.2f}%"
    except (ValueError, TypeError):
        return "N/A"


class MarketFindings(LLMOutputBase):
    price_momentum: str = Field(description="Price trend relative to 52-week range")
    valuation_assessment: str = Field(description="Is the stock cheap, fair, or expensive vs typical sector multiples")
    sector_position: str = Field(description="Company's standing within its sector based on available data")
    dividend_assessment: str = Field(description="Dividend yield attractiveness for income investors")
    key_risks: list[str] = Field(description="Top 2 market/sector risks")
    key_opportunities: list[str] = Field(description="Top 2 market opportunities")
    confidence: float = Field(description="0.0-1.0 confidence in this assessment")


def _build_prompt(company: str, stock: dict) -> str:
    current = stock.get("current_price", "N/A")
    high = stock.get("52w_high", "N/A")
    low = stock.get("52w_low", "N/A")

    return (
        f"Analyse the market positioning of {company} ({stock['ticker']}).\n\n"
        f"=== PRICE DATA ===\n"
        f"  Current price: {current}\n"
        f"  52-week high:  {high}\n"
        f"  52-week low:   {low}\n"
        f"  P/E ratio:     {stock.get('pe_ratio', 'N/A')}\n"
        f"  P/B ratio:     {stock.get('pb_ratio', 'N/A')}\n"
        f"  Dividend yield:{stock.get('dividend_yield', 'N/A')}\n"
        f"  Analyst rating:{stock.get('analyst_rating', 'N/A')}\n\n"
        f"=== COMPANY CONTEXT ===\n"
        f"  Sector:   {stock.get('sector', 'N/A')}\n"
        f"  Industry: {stock.get('industry', 'N/A')}\n"
        f"  Market cap: {stock.get('market_cap', 'N/A')}\n\n"
        f"Produce a structured market analysis using ONLY the data above."
    )


class MarketAgent(Agent):
    name = "market"

    async def run(self, company: str, ticker: str) -> AgentResult:
        logger.info("market_agent_start", company=company, ticker=ticker)

        stock_data = await fetch_stock_data(ticker)

        citations = [
            Citation(source="yfinance", label="Current Price", value=stock_data["current_price"],
                     url=f"https://finance.yahoo.com/quote/{ticker}"),
            Citation(source="yfinance", label="52W High/Low",
                     value=f"{stock_data['52w_high']} / {stock_data['52w_low']}",
                     url=f"https://finance.yahoo.com/quote/{ticker}"),
            Citation(source="yfinance", label="Analyst Rating", value=stock_data["analyst_rating"],
                     url=f"https://finance.yahoo.com/quote/{ticker}/analysis"),
        ]

        prompt = _build_prompt(company, stock_data)
        try:
            findings = await parse_response(MarketFindings, prompt, system=SYSTEM_PROMPT)
            logger.info("market_agent_done", company=company)
            return AgentResult(
                agent_name=self.name,
                company=company,
                findings=findings.model_dump(),
                evidence={"stock": stock_data},
                citations=citations,
            )
        except Exception as exc:
            logger.error("market_agent_failed", company=company, error=str(exc))
            return AgentResult(
                agent_name=self.name,
                company=company,
                evidence={"stock": stock_data},
                citations=citations,
                error=str(exc),
            )
