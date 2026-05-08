import hashlib
import json
import aiofiles
import aiofiles.os
import structlog
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings

logger = structlog.get_logger()


def cache_key(model: str, prompt: str, system: str | None, json_mode: bool) -> str:
    """
    Produce a deterministic fingerprint for a unique LLM request.
    Same inputs → same key → same cache file, every time.
    """
    payload = f"{model}|{system or ''}|{prompt}|{json_mode}"
    return hashlib.sha256(payload.encode()).hexdigest()


def _cache_path(key: str) -> Path:
    return Path(settings.cache_dir) / "llm" / f"{key}.json"


async def get_cached(key: str) -> str | None:
    """Return the cached LLM response string, or None on a cache miss."""
    path = _cache_path(key)
    try:
        async with aiofiles.open(path) as f:
            data = json.loads(await f.read())
        logger.debug("llm_cache_hit", hash=key[:8])
        return data["response"]
    except FileNotFoundError:
        logger.debug("llm_cache_miss", hash=key[:8])
        return None


async def set_cached(key: str, prompt: str, model: str, response: str) -> None:
    """Persist an LLM response to disk so future identical calls are free."""
    path = _cache_path(key)
    path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "prompt_hash": key,
        "model": model,
        "prompt": prompt,
        "response": response,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    async with aiofiles.open(path, "w") as f:
        await f.write(json.dumps(entry, indent=2))
