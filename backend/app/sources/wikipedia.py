"""
Fetches a company's Wikipedia summary as background context for the LLM.

Why Wikipedia?
- Free, no API key, covers every major Indian listed company.
- Gives the LLM context about the company's history, segments, and subsidiaries
  that may not appear in financial data alone.
- 500-word summary is enough context without blowing up the prompt length.
"""
import asyncio
import structlog
import wikipediaapi

logger = structlog.get_logger()

_wiki = wikipediaapi.Wikipedia(
    language="en",
    user_agent="Meridian/0.1 (due-diligence-research-tool; contact: research@meridian.local)",
)


def _fetch_summary_sync(company: str) -> dict:
    """Synchronous Wikipedia fetch — runs in a thread pool."""
    page = _wiki.page(company)

    if not page.exists():
        logger.warning("wikipedia_page_not_found", company=company)
        return {"found": False, "summary": "", "url": ""}

    summary = page.summary[:1500]  # keep it tight — we don't need the full article
    logger.info("wikipedia_fetch_done", company=company, chars=len(summary))

    return {
        "found": True,
        "title": page.title,
        "summary": summary,
        "url": page.fullurl,
    }


async def fetch_summary(company: str) -> dict:
    """
    Fetch the Wikipedia summary for `company`.

    Args:
        company: The search term, e.g. "Reliance Industries" or "Tata Consultancy Services"
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch_summary_sync, company)
