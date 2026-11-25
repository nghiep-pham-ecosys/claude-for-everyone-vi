"""Exercise 3: a complete tool loop.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
vong_lap = loop, cau_hoi = question, max_luot = maximum turns.

vong_lap(client, cau_hoi, tools, registry, max_luot=5) -> the last Message
    - Start with messages = [a user turn with cau_hoi].
    - Each turn: client.create(messages=..., tools=tools).
      If stop_reason is not "tool_use" -> return that message.
    - Otherwise: append the assistant turn with msg.content UNCHANGED (the mock returns 400 if you drop
      the thinking block), then ONE user turn with a tool_result for EVERY tool_use (use chay_tool from
      exercise 2), in the same order.
    - max_luot is the maximum number of API calls. Out of turns and still "tool_use" -> raise RuntimeError.

Grade:  CHAM="$PWD/en/modules/03-tool-use/exercises" uv run pytest modules/03-tool-use -q
"""
from __future__ import annotations

import importlib.util
from collections.abc import Callable
from pathlib import Path
from typing import Any

from anthropic.types import Message

from claude_vi import ClaudeVi

# Reuse chay_tool from your own exercise 2
_spec = importlib.util.spec_from_file_location("bai2_cua_ban", Path(__file__).with_name("bai2_chay_tool.py"))
_bai2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bai2)
chay_tool = _bai2.chay_tool


def vong_lap(client: ClaudeVi, cau_hoi: str, tools: list[dict[str, Any]],
             registry: dict[str, Callable[..., Any]], max_luot: int = 5) -> Message:
    raise NotImplementedError("TODO: exercise 3")
