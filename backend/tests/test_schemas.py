"""
Tests for structured LLM output parsing and the retry mechanism.

We mock `complete()` so these tests never call Ollama.
That makes them fast, free, and deterministic.
"""
import pytest
from unittest.mock import AsyncMock, patch
from pydantic import BaseModel
from app.llm.schemas import parse_response


class SampleOutput(BaseModel):
    company: str
    score: int


PATCH_TARGET = "app.llm.schemas.complete"


async def test_parse_valid_json_on_first_try():
    with patch(PATCH_TARGET, new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = '{"company": "Reliance", "score": 85}'

        result = await parse_response(SampleOutput, "analyse Reliance")

        assert result.company == "Reliance"
        assert result.score == 85
        assert mock_complete.call_count == 1  # no retry needed


async def test_parse_retries_on_bad_json():
    """First call returns garbage; second call returns valid JSON."""
    with patch(PATCH_TARGET, new_callable=AsyncMock) as mock_complete:
        mock_complete.side_effect = [
            "Sure! Here is my analysis of Reliance...",   # bad — plain text, not JSON
            '{"company": "TCS", "score": 90}',            # good
        ]

        result = await parse_response(SampleOutput, "analyse TCS")

        assert result.company == "TCS"
        assert mock_complete.call_count == 2  # retried exactly once


async def test_parse_raises_after_two_failures():
    """Both attempts return garbage — should raise, not loop forever."""
    with patch(PATCH_TARGET, new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = "this is not json at all"

        with pytest.raises(Exception):
            await parse_response(SampleOutput, "analyse Infosys")

        assert mock_complete.call_count == 2  # tried twice, gave up


async def test_retry_prompt_contains_schema():
    """Verify the retry prompt includes the JSON schema so the model knows what to fix."""
    with patch(PATCH_TARGET, new_callable=AsyncMock) as mock_complete:
        mock_complete.side_effect = [
            "oops not json",
            '{"company": "HDFC", "score": 88}',
        ]

        await parse_response(SampleOutput, "analyse HDFC")

        retry_call_prompt = mock_complete.call_args_list[1][0][0]
        assert "schema" in retry_call_prompt.lower() or "company" in retry_call_prompt
