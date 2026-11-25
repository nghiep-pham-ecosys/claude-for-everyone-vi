"""Bài 2 — host nối NHIỀU MCP server với Claude: đặt tên tool không trùng, đúng luật Messages API. (LỜI GIẢI)"""
from __future__ import annotations

import re
from typing import Any

KY_TU_SAI = re.compile(r"[^a-zA-Z0-9_-]")


def sang_tool_claude(tools: list[Any], tien_to: str) -> tuple[list[dict[str, Any]], dict[str, str]]:
    if not tien_to:
        raise ValueError("tien_to không được rỗng")
    ds, bang = [], {}
    for t in tools:
        ten = KY_TU_SAI.sub("_", f"{tien_to}__{t.name}")[:128]
        if ten in bang:
            raise ValueError(f"Hai tool cùng ra tên '{ten}': '{bang[ten]}' và '{t.name}'")
        bang[ten] = t.name
        ds.append({"name": ten, "description": t.description or "", "input_schema": t.input_schema})
    return ds, bang
