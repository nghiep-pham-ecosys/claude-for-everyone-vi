"""Bài 1 — đọc luồng message của một lần chạy agent. (LỜI GIẢI)"""
from __future__ import annotations

from types import ModuleType
from typing import Any


def tom_tat(sdk: ModuleType, messages: list[Any]) -> dict[str, Any]:
    ket_qua = [m for m in messages if isinstance(m, sdk.ResultMessage)]
    if not ket_qua:
        raise ValueError("Không có ResultMessage: đọc luồng chưa hết?")
    r = ket_qua[-1]
    tools = [b.name for m in messages if isinstance(m, sdk.AssistantMessage)
             for b in m.content if isinstance(b, sdk.ToolUseBlock)]
    loi = sum(1 for m in messages if isinstance(m, sdk.UserMessage) and isinstance(m.content, list)
              for b in m.content if isinstance(b, sdk.ToolResultBlock) and b.is_error is True)
    return {"session_id": r.session_id, "tools_da_goi": tools, "tool_loi": loi, "so_luot": r.num_turns,
            "usd": r.total_cost_usd, "tra_loi": r.result,
            "thanh_cong": r.subtype == "success" and not r.is_error}
