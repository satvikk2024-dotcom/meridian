import httpx
import structlog

from app.config import settings
from app.llm.cache import cache_key, get_cached, set_cached

logger = structlog.get_logger()


async def complete(
    prompt: str,
    system: str | None = None,
    json_mode: bool = False,
    model: str | None = None,
) -> str:
    """
    Send a prompt to the configured LLM and return the response text.

    Checks the disk cache first — a cache hit costs ~1ms and zero compute.
    Cache misses call Ollama, then write to disk before returning.

    Args:
        prompt:    The user message.
        system:    Optional system prompt (sets agent persona/instructions).
        json_mode: If True, instructs the model to output valid JSON only.
        model:     Override the default model from settings.
    """
    resolved_model = model or settings.ollama_model
    key = cache_key(resolved_model, prompt, system, json_mode)

    if settings.cache_llm_calls:
        cached = await get_cached(key)
        if cached is not None:
            return cached

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload: dict = {"model": resolved_model, "messages": messages, "stream": False}
    if json_mode:
        payload["format"] = "json"

    logger.info("llm_call_start", model=resolved_model, json_mode=json_mode)

    async with httpx.AsyncClient(
        base_url=settings.ollama_base_url,
        timeout=httpx.Timeout(120.0),  # 7B models can be slow on first token
    ) as client:
        response = await client.post("/api/chat", json=payload)
        response.raise_for_status()
        text: str = response.json()["message"]["content"]

    logger.info("llm_call_done", model=resolved_model, chars=len(text))

    if settings.cache_llm_calls:
        await set_cached(key, prompt, resolved_model, text)

    return text
