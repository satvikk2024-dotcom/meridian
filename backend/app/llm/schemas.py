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


def _build_example_template(model_class: Type[T]) -> str:
    """
    Build a simple JSON template from a Pydantic model.

    Shows field names with placeholder values that match the field type
    (e.g. "<string>", ["<string>", ...], 0.0 for float).
    Small models follow concrete examples far better than abstract schemas.
    """
    schema = model_class.model_json_schema()
    props = schema.get("properties", {})
    example: dict = {}
    for field_name, field_info in props.items():
        t = field_info.get("type")
        items = field_info.get("items", {})
        if t == "array":
            item_type = items.get("type", "string")
            example[field_name] = [f"<{item_type}>"]
        elif t == "number" or t == "integer":
            example[field_name] = 0.0 if t == "number" else 0
        elif t == "boolean":
            example[field_name] = False
        else:
            example[field_name] = f"<{field_info.get('description', 'string')}>"
    return json.dumps(example, indent=2)


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

    # Build a corrective prompt using a concrete example template.
    # We avoid dumping the raw JSON schema because small models (qwen2.5:7b) confuse
    # schema annotations (description/type) with the actual output values they should write.
    example = _build_example_template(model_class)
    retry_prompt = (
        f"{prompt}\n\n"
        f"IMPORTANT: Your previous response could not be parsed. "
        f"You MUST respond with a JSON object that looks EXACTLY like this template "
        f"(replace placeholder values with real content):\n"
        f"{example}\n"
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
