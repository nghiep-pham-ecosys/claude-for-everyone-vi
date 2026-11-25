"""Bài 3 — host quyết định duyệt và trả kết quả tool MCP cho Claude. (LỜI GIẢI)"""
from __future__ import annotations

import json
from typing import Any


def can_duyet(tool: Any, cho_chay: set[str]) -> bool:
    if tool.name not in cho_chay:
        return True
    a = tool.annotations
    return bool(a and a.destructive_hint is True)


def sang_tool_result(tool_use_id: str, ket_qua: Any) -> dict[str, Any]:
    chu = [{"type": "text", "text": c.text} for c in ket_qua.content if getattr(c, "type", None) == "text"]
    if not chu and ket_qua.structured_content is not None:
        chu = [{"type": "text", "text": json.dumps(ket_qua.structured_content, ensure_ascii=False)}]
    if not chu:
        chu = [{"type": "text", "text": "(không có nội dung)"}]
    return {"type": "tool_result", "tool_use_id": tool_use_id, "is_error": bool(ket_qua.is_error), "content": chu}
