"""Exercise 3: the host decides on approval and returns MCP tool results to Claude.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
can_duyet = needs approval, cho_chay = allowed to run, sang_tool_result = to tool_result, ket_qua = result.

can_duyet(tool, cho_chay) -> bool      (True = ask the user before the call)
    tool: mcp.types.Tool; cho_chay: the set of tool names that the HOST lets run without asking.
    - tool.name is not in cho_chay: True, WHATEVER the annotations say (server annotations are not trusted).
    - tool.name is in cho_chay but the annotations set destructive_hint to True (an EXPLICIT value): True.
      The rule of this exercise: with a server you do not trust yet, annotations may only make the host more
      careful. No annotations, or destructive_hint is None: ignore it, because the host already trusts the
      tools in cho_chay (even though the spec treats destructiveHint as true by default).
    - otherwise: False.

sang_tool_result(tool_use_id, ket_qua) -> dict   (ket_qua: mcp.types.CallToolResult)
    {"type": "tool_result", "tool_use_id": ..., "is_error": bool(ket_qua.is_error), "content": [...]}
    content: each block of type "text" in ket_qua.content becomes {"type": "text", "text": ...} (keep the
    order, drop every other block such as image, audio, resource; do not read c.text of a block that is not
    text). No text block and structured_content is not None: one text block with
    json.dumps(structured_content, ensure_ascii=False) (even when structured_content is {} or another empty
    value). Nothing at all: one text block "(không có nội dung)" (Vietnamese for "(no content)"; the shared
    test checks this exact string).

Grade:  CHAM="$PWD/en/modules/10-mcp/exercises" CLAUDE_MOCK=1 uv run pytest modules/10-mcp -q
"""
from __future__ import annotations

from typing import Any


def can_duyet(tool: Any, cho_chay: set[str]) -> bool:
    raise NotImplementedError("TODO: exercise 3")


def sang_tool_result(tool_use_id: str, ket_qua: Any) -> dict[str, Any]:
    raise NotImplementedError("TODO: exercise 3")
