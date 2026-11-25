"""Exercise 2: a host bridges SEVERAL MCP servers to Claude. Tool names must not clash and must follow the
Messages API rule.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
sang_tool_claude = to Claude tools, tien_to = prefix, ten_claude = the name Claude sees.

sang_tool_claude(tools, tien_to) -> tuple[list[dict], dict[str, str]]
    tools: a list of mcp.types.Tool from ONE server; tien_to: a short name for the server, for example "ptn".
    Each tool -> {"name": ten_claude, "description": t.description or "", "input_schema": t.input_schema}.
    ten_claude = f"{tien_to}__{t.name}", then:
      - replace every character that is NOT in [a-zA-Z0-9_-] with "_";
      - cut it to at most 128 characters (the Messages API rule for tool names).
    Return (the tool list for Claude, a map ten_claude -> original MCP name), so you can call the right tool
    on the server later. Two tools end up with the same ten_claude: raise ValueError. Empty tien_to: raise
    ValueError.

Grade:  CHAM="$PWD/en/modules/10-mcp/exercises" CLAUDE_MOCK=1 uv run pytest modules/10-mcp -q
"""
from __future__ import annotations

from typing import Any


def sang_tool_claude(tools: list[Any], tien_to: str) -> tuple[list[dict[str, Any]], dict[str, str]]:
    raise NotImplementedError("TODO: exercise 2")
