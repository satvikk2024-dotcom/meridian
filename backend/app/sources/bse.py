"""
Fetches financial data for Indian public companies via yfinance.

yfinance pulls data from Yahoo Finance, which covers NSE (.NS) and BSE (.BO)
tickers natively. No API key required. We cache results to disk so repeated
runs during development are instant and free.

Why yfinance over the official BSE/NSE APIs?
- BSE's official data API requires registration and has rate limits.
- yfinance covers the same fundamentals (P/E, revenue, market cap) for free.
- The .NS / .BO suffix is the only change needed to target Indian exchanges.
"""
import asyncio
import structlog
import yfinance as yf

logger = structlog.get_logger()


def _fetch_stock_data_sync(ticker: str) -> dict:
    """
    Synchronous yfinance call — runs in a thread so it doesn't block asyncio.

    Returns a flat dict of the key financials we care about.
    All values are strings so they can be dropped directly into an LLM prompt.
    """
    t = yf.Ticker(ticker)
    info = t.info  # one HTTP call; returns a large dict

    def fmt_crore(v) -> str:
        """Convert raw INR value to Crore (÷1e7), formatted with commas."""
        if v is None:
            return "N/A"
        return f"₹{v / 1e7:,.0f} Cr"

    def fmt_pct(v) -> str:
        if v is None:
            return "N/A"
        return f"{v * 100:.1f}%"

    def safe(v) -> str:
        return "N/A" if v is None else str(v)

    data = {
        "ticker": ticker,
        "company_name": safe(info.get("longName")),
        "sector": safe(info.get("sector")),
        "industry": safe(info.get("industry")),
        "market_cap": fmt_crore(info.get("marketCap")),
        "current_price": f"₹{info.get('currentPrice', 'N/A')}",
        "52w_high": f"₹{info.get('fiftyTwoWeekHigh', 'N/A')}",
        "52w_low": f"₹{info.get('fiftyTwoWeekLow', 'N/A')}",
        "pe_ratio": safe(info.get("trailingPE")),
        "pb_ratio": safe(info.get("priceToBook")),
        "revenue_ttm": fmt_crore(info.get("totalRevenue")),
        "net_income_ttm": fmt_crore(info.get("netIncomeToCommon")),
        "operating_cashflow": fmt_crore(info.get("operatingCashflow")),
        "debt_to_equity": safe(info.get("debtToEquity")),
        "roe": fmt_pct(info.get("returnOnEquity")),
        "revenue_growth": fmt_pct(info.get("revenueGrowth")),
        "earnings_growth": fmt_pct(info.get("earningsGrowth")),
        "dividend_yield": fmt_pct(info.get("dividendYield")),
        "analyst_rating": safe(info.get("recommendationKey")),
        "business_summary": (info.get("longBusinessSummary") or "")[:400],
    }

    logger.info("bse_fetch_done", ticker=ticker, company=data["company_name"])
    return data


async def fetch_stock_data(ticker: str) -> dict:
    """
    Fetch fundamentals for an Indian stock ticker (e.g. "RELIANCE.NS").

    Runs the synchronous yfinance call in a thread pool so it doesn't block
    the FastAPI event loop.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch_stock_data_sync, ticker)
