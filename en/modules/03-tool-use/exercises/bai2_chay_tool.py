"""Exercise 2: turn one tool_use into a tool_result.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
chay_tool = run a tool.

chay_tool(block, registry) -> tool_result dict
    block: one tool_use block from msg.content (it has .id, .name, .input).
    registry: {tool name: Python function}.

    - Always has "type": "tool_result" and "tool_use_id": block.id.
    - The tool is not in the registry -> "is_error": True, and the content names the wrong tool AND lists
      the tools that exist (a useful message helps Claude fix itself).
    - The function raises an exception -> "is_error": True, content like "ErrorName: message"
      (for example "ValueError: ..."). Do NOT let the exception escape.
    - Success: content is a string; if the result is not a str, use json.dumps(..., ensure_ascii=False).
      No "is_error" key (or False).

Grade:  CHAM="$PWD/en/modules/03-tool-use/exercises" uv run pytest modules/03-tool-use -q
"""
from __future__ import annotations

import json  # noqa: F401
from collections.abc import Callable
from typing import Any


def chay_tool(block: Any, registry: dict[str, Callable[..., Any]]) -> dict[str, Any]:
    raise NotImplementedError("TODO: exercise 2")
