"""Nạp Claude Agent SDK cho module 09: mock khi CLAUDE_MOCK=1, gói thật `claude_agent_sdk` khi chạy thật.

    sdk = nap_sdk()
    async for msg in sdk.query(prompt="...", options=sdk.ClaudeAgentOptions(max_turns=3)):
        ...

Gói thật KHÔNG nằm trong dependency của repo: mỗi wheel khoảng 165–178 MB vì kèm Claude Code CLI (PyPI, kiểm
2026-11-25). Cài khi cần chạy thật: `uv pip install claude-agent-sdk`.
"""
from __future__ import annotations

from types import ModuleType

from .config import Settings


class MissingSdkError(RuntimeError):
    """Chạy thật mà chưa cài claude-agent-sdk."""


def nap_sdk(settings: Settings | None = None) -> ModuleType:
    if (settings or Settings.from_env()).mock:
        from . import agent_sdk_mock

        return agent_sdk_mock
    try:
        import claude_agent_sdk
    except ImportError as e:
        raise MissingSdkError(
            "Chưa cài Claude Agent SDK. Chạy không cần SDK: đặt CLAUDE_MOCK=1. "
            "Chạy thật: uv pip install claude-agent-sdk (gói khoảng 170 MB, kèm Claude Code CLI), "
            "rồi đặt ANTHROPIC_API_KEY (SDK không tự đọc .env; claude_vi nạp .env giúp bạn)."
        ) from e
    return claude_agent_sdk
