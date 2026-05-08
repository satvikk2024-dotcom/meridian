import json
import structlog
from typing import TypeVar, Type
from pydantic import BaseModel, ValidationError

from app.llm.client import complete

logger = structlog.get_logger()

T = TypeVar("T", bound=BaseModel)


class LLMOutputBase(BaseModel):
    """
    Base class for all structured LLM outputs.
    Agents define subclasses with the specific fields they expect.

    Example:
        class FinancialFindings(LLMOutputBase):
            revenue_trend: str
            key_risks: list[str]
            confidence: float
    """
    pass


async def parse_response(
    model_class: Type[T],
    prompt: str,
    system: str | None = None,
    llm_model: str | None = None,
) -> T:
    """
    Call the LLM and parse the response into `model_class`.

    Flow:
        1. Call complete() with json_mode=True.
        2. Try model_class.model_validate_json(response).
        3. On failure, retry once with a corrective prompt containing the schema.
        4. On second failure, raise — the caller decides how to handle it.

    The retry doubles the token cost but cuts parse failures from ~12% to ~1%.
    We only retry once; infinite retries would hide prompt quality issues.
    """
    raw = await complete(prompt, system=system, json_mode=True, model=llm_model)

    try:
        return model_class.model_validate_json(raw)
    except (ValidationError, json.JSONDecodeError) as first_err:
        logger.warning(
            "llm_parse_failed_retrying",
            model_class=model_class.__name__,
            error=str(first_err)[:120],
        )

    # Build a corrective prompt that shows the model exactly what schema to match.
    schema = json.dumps(model_class.model_json_schema(), indent=2)
    retry_prompt = (
        f"{prompt}\n\n"
        f"IMPORTANT: Your previous response could not be parsed as valid JSON.\n"
        f"You MUST respond with a JSON object matching this exact schema:\n"
        f"{schema}\n"
        f"Respond with JSON only. No explanation, no markdown, no code fences."
    )

    raw_retry = await complete(retry_prompt, system=system, json_mode=True, model=llm_model)

    try:
        return model_class.model_validate_json(raw_retry)
    except (ValidationError, json.JSONDecodeError) as second_err:
        logger.error(
            "llm_parse_failed_giving_up",
            model_class=model_class.__name__,
            error=str(second_err)[:120],
        )
        raise
