"""
Fetches recent Reddit posts mentioning a company from r/IndiaInvestments
and r/IndianStockMarket using Reddit's public JSON API.

Why Reddit?
- Free, no OAuth needed for read-only public posts (just append .json to any URL).
- r/IndiaInvestments has active retail investor discussion on Indian stocks.
- Retail sentiment is a real signal used by hedge funds (see: WSB saga).

Why not the official Reddit API?
- OAuth setup is overkill for an MVP. The public .json endpoint is rate-limited
  but sufficient for a demo that fetches ~10 posts per run.
- ADR note: if we need more volume, swap in PRAW (Python Reddit API Wrapper).
"""
import asyncio
import structlog
import httpx

logger = structlog.get_logger()

SUBREDDITS = ["IndiaInvestments", "IndianStockMarket"]
REDDIT_HEADERS = {"User-Agent": "Meridian/0.1 due-diligence-research-tool"}


async def fetch_mentions(company: str, max_posts: int = 10) -> dict:
    """
    Search Reddit for recent posts mentioning `company`.

    Returns a dict with posts (title + snippet) and the subreddits searched.
    We use Reddit's built-in search endpoint — no API key needed.
    """
    # Search across both subreddits in parallel
    tasks = [_search_subreddit(sr, company, max_posts) for sr in SUBREDDITS]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    posts = []
    for sr, result in zip(SUBREDDITS, results):
        if isinstance(result, Exception):
            logger.warning("reddit_fetch_failed", subreddit=sr, error=str(result))
            continue
        posts.extend(result)

    posts = posts[:max_posts]
    logger.info("reddit_fetch_done", company=company, post_count=len(posts))
    return {"posts": posts, "subreddits_searched": SUBREDDITS}


async def _search_subreddit(subreddit: str, query: str, limit: int) -> list[dict]:
    """Search one subreddit via the public JSON API."""
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    params = {"q": query, "sort": "new", "limit": limit, "restrict_sr": "true"}

    async with httpx.AsyncClient(headers=REDDIT_HEADERS, timeout=15.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    posts = []
    for child in data.get("data", {}).get("children", []):
        p = child["data"]
        posts.append({
            "title": p.get("title", ""),
            "score": p.get("score", 0),
            "num_comments": p.get("num_comments", 0),
            "url": f"https://reddit.com{p.get('permalink', '')}",
            "selftext": (p.get("selftext") or "")[:300],  # first 300 chars of post body
        })
    return posts
