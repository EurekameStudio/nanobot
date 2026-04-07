"""Tests for Gemini INVALID_ARGUMENT fix via Feishu channel.

Two root causes were identified and fixed:

1. ``stream_options={"include_usage": True}`` was sent unconditionally in every
   streaming call (``chat_stream``).  Feishu enables streaming by default.
   **Fix**: skip ``stream_options`` when ``spec.name == "gemini"``.

2. ``reasoning_content`` and ``extra_content`` (at message level) were kept in
   ``_ALLOWED_MSG_KEYS`` and survived ``_sanitize_messages()``.  If conversation
   history contained assistant messages from a prior turn with these fields,
   they were forwarded to Gemini which rejects them.
   **Fix**: strip ``reasoning_content`` and message-level ``extra_content`` in
   ``_sanitize_messages()`` when ``spec.name == "gemini"``.

Note: ``extra_content`` inside ``tool_calls`` entries is preserved — that is the
Gemini thought-signature round-trip and must survive for multi-turn tool use.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from nanobot.providers.openai_compat_provider import OpenAICompatProvider
from nanobot.providers.registry import find_by_name


def _gemini_provider(**overrides) -> OpenAICompatProvider:
    spec = find_by_name("gemini")
    with patch("nanobot.providers.openai_compat_provider.AsyncOpenAI"):
        return OpenAICompatProvider(
            api_key="test-key",
            api_base="https://generativelanguage.googleapis.com/v1beta/openai/",
            default_model="gemini-2.0-flash",
            spec=spec,
            **overrides,
        )


def _fake_chat_response(content: str = "Hello!") -> SimpleNamespace:
    message = SimpleNamespace(content=content, tool_calls=None, reasoning_content=None)
    choice = SimpleNamespace(message=message, finish_reason="stop")
    usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    return SimpleNamespace(choices=[choice], usage=usage)


def _fake_stream_chunks(content: str = "Hello!") -> list:
    delta = SimpleNamespace(content=content, tool_calls=None, reasoning_content=None)
    choice = SimpleNamespace(finish_reason="stop", delta=delta)
    usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    return [
        SimpleNamespace(choices=[choice], usage=None),
        SimpleNamespace(choices=[], usage=usage),
    ]


class _FakeAsyncStream:
    def __init__(self, chunks):
        self._chunks = iter(chunks)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._chunks)
        except StopIteration:
            raise StopAsyncIteration


# ---------------------------------------------------------------------------
# Fix 1: stream_options must NOT be sent to Gemini
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_gemini_stream_call_omits_stream_options() -> None:
    """chat_stream() should NOT send stream_options for Gemini."""
    provider = _gemini_provider()
    mock_create = AsyncMock(return_value=_FakeAsyncStream(_fake_stream_chunks()))
    provider._client.chat.completions.create = mock_create

    await provider.chat_stream(
        messages=[{"role": "user", "content": "hi"}],
        model="gemini-2.0-flash",
    )

    call_kwargs = mock_create.call_args.kwargs
    assert call_kwargs["stream"] is True
    assert "stream_options" not in call_kwargs, (
        "stream_options must not be sent to Gemini — it triggers INVALID_ARGUMENT"
    )


@pytest.mark.asyncio
async def test_openai_stream_call_includes_stream_options() -> None:
    """Non-Gemini providers should still get stream_options."""
    spec = find_by_name("openai")
    with patch("nanobot.providers.openai_compat_provider.AsyncOpenAI") as mock_client:
        provider = OpenAICompatProvider(
            api_key="sk-test",
            default_model="gpt-4o",
            spec=spec,
        )
        mock_create = AsyncMock(return_value=_FakeAsyncStream(_fake_stream_chunks()))
        mock_client.return_value.chat.completions.create = mock_create

        await provider.chat_stream(
            messages=[{"role": "user", "content": "hi"}],
            model="gpt-4o",
        )

        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["stream_options"] == {"include_usage": True}


def test_build_kwargs_does_not_include_stream_options() -> None:
    """_build_kwargs (non-streaming path) should never contain stream_options."""
    provider = _gemini_provider()
    kwargs = provider._build_kwargs(
        messages=[{"role": "user", "content": "hi"}],
        tools=None,
        model="gemini-2.0-flash",
        max_tokens=4096,
        temperature=0.7,
        reasoning_effort=None,
        tool_choice=None,
    )
    assert "stream_options" not in kwargs
    assert "stream" not in kwargs


# ---------------------------------------------------------------------------
# Fix 2a: reasoning_content stripped from messages for Gemini
# ---------------------------------------------------------------------------


def test_gemini_sanitize_strips_reasoning_content() -> None:
    """reasoning_content on assistant messages should be stripped for Gemini."""
    provider = _gemini_provider()

    messages = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Think step by step"},
        {
            "role": "assistant",
            "content": "The answer is 42.",
            "reasoning_content": "Step 1: parse. Step 2: compute.",
        },
        {"role": "user", "content": "Thanks, now say hi."},
    ]

    sanitized = provider._sanitize_messages(messages)
    assistant_msg = [m for m in sanitized if m["role"] == "assistant"][0]
    assert "reasoning_content" not in assistant_msg, (
        "reasoning_content must be stripped for Gemini — it triggers INVALID_ARGUMENT"
    )
    assert assistant_msg["content"] == "The answer is 42."


def test_gemini_build_kwargs_strips_reasoning_content() -> None:
    """_build_kwargs should not include reasoning_content in messages for Gemini."""
    provider = _gemini_provider()

    messages = [
        {"role": "system", "content": "You are helpful."},
        {
            "role": "assistant",
            "content": "done",
            "reasoning_content": "thinking...",
        },
        {"role": "user", "content": "hi"},
    ]

    kwargs = provider._build_kwargs(
        messages=messages,
        tools=None,
        model="gemini-2.0-flash",
        max_tokens=4096,
        temperature=0.7,
        reasoning_effort=None,
        tool_choice=None,
    )

    sent_messages = kwargs["messages"]
    assistant_msg = [m for m in sent_messages if m["role"] == "assistant"][0]
    assert "reasoning_content" not in assistant_msg


# ---------------------------------------------------------------------------
# Fix 2b: extra_content at message level stripped for Gemini
# ---------------------------------------------------------------------------


def test_gemini_sanitize_strips_message_level_extra_content() -> None:
    """extra_content at the top level of a message should be stripped for Gemini."""
    provider = _gemini_provider()

    messages = [
        {
            "role": "assistant",
            "content": "result",
            "extra_content": {"debug": True},
        },
        {"role": "user", "content": "next question"},
    ]

    sanitized = provider._sanitize_messages(messages)
    assert "extra_content" not in sanitized[0], (
        "message-level extra_content must be stripped for Gemini"
    )


def test_gemini_preserves_extra_content_inside_tool_calls() -> None:
    """extra_content INSIDE tool_calls entries must be preserved for Gemini
    — it is the thought-signature round-trip."""
    provider = _gemini_provider()

    messages = [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "fn", "arguments": "{}"},
                    "extra_content": {"google": {"thought_signature": "sig-abc"}},
                }
            ],
        },
        {"role": "user", "content": "continue"},
    ]

    sanitized = provider._sanitize_messages(messages)
    tc = sanitized[0]["tool_calls"][0]
    assert tc["extra_content"] == {"google": {"thought_signature": "sig-abc"}}, (
        "extra_content inside tool_calls must survive for Gemini thought-signature round-trip"
    )


# ---------------------------------------------------------------------------
# End-to-end: Gemini API succeeds with the fix
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_gemini_stream_succeeds_without_stream_options() -> None:
    """With the fix, chat_stream should succeed and not send stream_options."""
    provider = _gemini_provider()
    mock_create = AsyncMock(return_value=_FakeAsyncStream(_fake_stream_chunks()))
    provider._client.chat.completions.create = mock_create

    result = await provider.chat_stream(
        messages=[{"role": "user", "content": "Hello from Feishu!"}],
        model="gemini-2.0-flash",
    )

    assert result.finish_reason == "stop"
    assert result.content == "Hello!"
    call_kwargs = mock_create.call_args.kwargs
    assert "stream_options" not in call_kwargs


@pytest.mark.asyncio
async def test_gemini_chat_succeeds_with_reasoning_content_in_history() -> None:
    """With the fix, Gemini chat succeeds even when history has reasoning_content."""
    provider = _gemini_provider()
    mock_create = AsyncMock(return_value=_fake_chat_response("Hi back!"))
    provider._client.chat.completions.create = mock_create

    messages = [
        {"role": "system", "content": "You are helpful."},
        {
            "role": "assistant",
            "content": "The answer is 42.",
            "reasoning_content": "thinking...",
        },
        {"role": "user", "content": "Thanks, now say hi."},
    ]

    result = await provider.chat(
        messages=messages,
        model="gemini-2.0-flash",
    )

    assert result.finish_reason == "stop"
    assert result.content == "Hi back!"

    call_kwargs = mock_create.call_args.kwargs
    sent_messages = call_kwargs["messages"]
    assistant_msg = [m for m in sent_messages if m["role"] == "assistant"][0]
    assert "reasoning_content" not in assistant_msg, (
        "reasoning_content must not be in messages sent to Gemini"
    )


# ---------------------------------------------------------------------------
# Verify: other providers that DO support these fields are unaffected
# ---------------------------------------------------------------------------


def test_openai_sanitize_preserves_reasoning_content() -> None:
    """OpenAI should continue to receive reasoning_content."""
    spec = find_by_name("openai")
    with patch("nanobot.providers.openai_compat_provider.AsyncOpenAI"):
        provider = OpenAICompatProvider(
            api_key="sk-test",
            default_model="gpt-4o",
            spec=spec,
        )

    messages = [
        {"role": "assistant", "content": "hi", "reasoning_content": "thought"},
    ]
    sanitized = provider._sanitize_messages(messages)
    assert sanitized[0]["reasoning_content"] == "thought"


def test_deepseek_sanitize_preserves_reasoning_content() -> None:
    """DeepSeek supports reasoning_content natively, it must be preserved."""
    spec = find_by_name("deepseek")
    with patch("nanobot.providers.openai_compat_provider.AsyncOpenAI"):
        provider = OpenAICompatProvider(
            api_key="sk-test",
            default_model="deepseek-chat",
            spec=spec,
        )

    messages = [
        {"role": "assistant", "content": "hi", "reasoning_content": "thought"},
    ]
    sanitized = provider._sanitize_messages(messages)
    assert sanitized[0]["reasoning_content"] == "thought"


def test_openai_sanitize_preserves_extra_content() -> None:
    """OpenAI should continue to receive message-level extra_content."""
    spec = find_by_name("openai")
    with patch("nanobot.providers.openai_compat_provider.AsyncOpenAI"):
        provider = OpenAICompatProvider(
            api_key="sk-test",
            default_model="gpt-4o",
            spec=spec,
        )

    messages = [
        {"role": "assistant", "content": "hi", "extra_content": {"debug": True}},
    ]
    sanitized = provider._sanitize_messages(messages)
    assert sanitized[0]["extra_content"] == {"debug": True}
