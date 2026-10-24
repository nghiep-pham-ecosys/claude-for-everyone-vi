"""Bài 2 — chạy một tool_use thành tool_result. (LỜI GIẢI)"""
from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def chay_tool(block: Any, registry: dict[str, Callable[..., Any]]) -> dict[str, Any]:
    ket_qua: dict[str, Any] = {"type": "tool_result", "tool_use_id": block.id}
    ham = registry.get(block.name)
    if ham is None:
        ket_qua |= {"content": f"Không có tool '{block.name}'. Các tool hiện có: {', '.join(sorted(registry))}.",
                    "is_error": True}
        return ket_qua
    try:
        output = ham(**block.input)
    except Exception as e:  # noqa: BLE001
        ket_qua |= {"content": f"{type(e).__name__}: {e}", "is_error": True}
        return ket_qua
    ket_qua["content"] = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)
    return ket_qua
