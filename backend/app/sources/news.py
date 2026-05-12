"""
Google News RSS fetcher for Indian company news.

Uses the public Google News RSS endpoint — no API key, no cost.
Returns recent headlines with publish dates, enabling recency scoring.

Why RSS instead of a news API?
- Zero cost, no rate limits for light use
- Returns `pubDate` per article → feeds the `fetched_at` field on Citation
- Sufficient for the demo: 5-8 recent headlines per company
"""
import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus
import urllib.request

import structlog

logger = structlog.get_logger()

_RSS_URL = (
    "https://news.google.com/rss/search"
    "?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
)
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MeridianBot/1.0)"}
_TIMEOUT = 10


async def fetch_news(company: str, max_items: int = 8) -> list[dict]:
    """
    Fetch recent news headlines for a company from Google News RSS.

    Returns a list of dicts with keys: title, url, source, published_at.
    Returns empty list on any failure — news is supplementary, not critical.
    """
    query = quote_plus(f"{company} India stock NSE")
    url = _RSS_URL.format(query=query)

    loop = asyncio.get_event_loop()
    try:
        raw = await loop.run_in_executor(None, lambda: _fetch_rss(url))
        items = _parse_rss(raw)[:max_items]
        logger.info("news_fetch_done", company=company, count=len(items))
        return items
    except Exception as exc:
        logger.warning("news_fetch_failed", company=company, error=str(exc))
        return []


def _fetch_rss(url: str) -> bytes:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return resp.read()


def _parse_rss(raw: bytes) -> list[dict]:
    root = ET.fromstring(raw)
    channel = root.find("channel")
    if channel is None:
        return []

    items = []
    for item in channel.findall("item"):
        title    = item.findtext("title", "").strip()
        link     = item.findtext("link", "").strip()
        pub_str  = item.findtext("pubDate", "")
        src_elem = item.find("source")
        source   = src_elem.text.strip() if src_elem is not None else "News"

        published_at: datetime = datetime.now(tz=timezone.utc)
        if pub_str:
            try:
                published_at = parsedate_to_datetime(pub_str)
            except Exception:
                pass

        if title and link:
            items.append({
                "title":        title,
                "url":          link,
                "source":       source,
                "published_at": published_at,
            })
    return items
