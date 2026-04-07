"""Tests for Gemini INVALID_ARGUMENT fix.

1. test_gemini_feishu_message_call — basic test with reasoning_content/extra_content in history.
2. test_gemini_feishu_text_message — simulates a Feishu text message round-trip.
"""

import os

import pytest

from nanobot.providers.openai_compat_provider import OpenAICompatProvider
from nanobot.providers.registry import find_by_name


@pytest.mark.skipif(not os.environ.get("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
async def test_gemini_feishu_message_call() -> None:
    spec = find_by_name("gemini")
    provider = OpenAICompatProvider(
        api_key=os.environ["GEMINI_API_KEY"],
        api_base="https://generativelanguage.googleapis.com/v1beta/openai/",
        default_model="gemini-3-flash",
        spec=spec,
    )

    messages = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Think step by step"},
        {
            "role": "assistant",
            "content": "The answer is 42.",
            "reasoning_content": "Step 1: parse. Step 2: compute.",
            "extra_content": {"debug": True},
        },
        {"role": "user", "content": "你好"},
    ]

    result = await provider.chat_stream(messages=messages, model="gemini-flash-latest")

    print(f"finish_reason: {result.finish_reason}")
    print(f"content: {result.content}")
    print(f"error_kind: {getattr(result, 'error_kind', None)}")
    print(f"full result: {result}")

    assert result.finish_reason == "stop", f"Got error: {result.content}"


@pytest.mark.skipif(not os.environ.get("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
async def test_gemini_feishu_text_message() -> None:
    """Simulate Feishu flow: user sends text '你好' -> agent assembles messages with
    prior assistant history (reasoning_content + extra_content) -> chat_stream to Gemini."""
    spec = find_by_name("gemini")
    provider = OpenAICompatProvider(
        api_key=os.environ["GEMINI_API_KEY"],
        api_base="https://generativelanguage.googleapis.com/v1beta/openai/",
        default_model="gemini-3-flash",
        spec=spec,
    )

    feishu_user_text = "你好"

    messages = [
        {"role": "system", "content": "You are helpful."},
        {
            "role": "assistant",
            "content": "The answer is 42.",
            "reasoning_content": "Step 1: parse. Step 2: compute.",
            "extra_content": {"debug": True},
        },
        {"role": "user", "content": feishu_user_text},
    ]

    result = await provider.chat_stream(messages=messages, model="gemini-flash-latest")

    print(f"[feishu_text] finish_reason: {result.finish_reason}")
    print(f"[feishu_text] content: {result.content}")
    print(f"[feishu_text] error_kind: {getattr(result, 'error_kind', None)}")

    assert result.finish_reason == "stop", f"Got error: {result.content}"
