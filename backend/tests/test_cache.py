"""
Tests for the LLM disk cache.

We don't want tests writing to the real data/cache directory,
so we use pytest's tmp_path fixture — a fresh temp directory per test.
"""
import pytest
from app.llm.cache import cache_key, get_cached, set_cached


@pytest.fixture(autouse=True)
def patch_cache_dir(tmp_path, monkeypatch):
    """Redirect all cache reads/writes to a temp directory for this test."""
    monkeypatch.setattr("app.llm.cache.settings.cache_dir", str(tmp_path))


async def test_cache_miss_returns_none():
    result = await get_cached("nonexistent_hash_that_will_never_exist")
    assert result is None


async def test_write_then_read_returns_same_value():
    key = cache_key("qwen2.5:7b", "What is revenue?", None, True)
    response = '{"revenue_trend": "growing", "confidence": 0.9}'

    await set_cached(key, "What is revenue?", "qwen2.5:7b", response)
    result = await get_cached(key)

    assert result == response


async def test_different_inputs_produce_different_keys():
    key1 = cache_key("qwen2.5:7b", "prompt A", None, False)
    key2 = cache_key("qwen2.5:7b", "prompt B", None, False)
    assert key1 != key2


async def test_same_inputs_produce_same_key():
    key1 = cache_key("qwen2.5:7b", "same prompt", "same system", True)
    key2 = cache_key("qwen2.5:7b", "same prompt", "same system", True)
    assert key1 == key2


async def test_json_mode_flag_changes_key():
    key_no_json = cache_key("qwen2.5:7b", "prompt", None, False)
    key_json    = cache_key("qwen2.5:7b", "prompt", None, True)
    assert key_no_json != key_json
