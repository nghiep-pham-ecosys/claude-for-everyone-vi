"""Bài 2 — host nối NHIỀU MCP server với Claude: đặt tên tool không trùng, đúng luật Messages API.

sang_tool_claude(tools, tien_to) -> tuple[list[dict], dict[str, str]]
    tools: danh sách mcp.types.Tool của MỘT server; tien_to: tên ngắn của server, ví dụ "ptn".
    Mỗi tool -> {"name": ten_claude, "description": t.description or "", "input_schema": t.input_schema}.
    ten_claude = f"{tien_to}__{t.name}", rồi:
      - mọi ký tự KHÔNG thuộc [a-zA-Z0-9_-] thay bằng "_";
      - cắt còn tối đa 128 ký tự (luật tên tool của Messages API).
    Trả về (danh sách tool cho Claude, bảng ten_claude -> tên MCP gốc) để gọi lại đúng tool trên server.
    Hai tool ra cùng một ten_claude: raise ValueError. tien_to rỗng: raise ValueError.

Chấm:  CHAM=exercises CLAUDE_MOCK=1 uv run pytest modules/10-mcp -q
"""
from __future__ import annotations

from typing import Any


def sang_tool_claude(tools: list[Any], tien_to: str) -> tuple[list[dict[str, Any]], dict[str, str]]:
    raise NotImplementedError("TODO: bài 2")
