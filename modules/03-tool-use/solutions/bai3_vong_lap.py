"""Bài 3 — vòng lặp tool hoàn chỉnh. (LỜI GIẢI)"""
from __future__ import annotations

import importlib.util
from collections.abc import Callable
from pathlib import Path
from typing import Any

from anthropic.types import Message

from claude_vi import ClaudeVi

_spec = importlib.util.spec_from_file_location("bai2_loi_giai", Path(__file__).with_name("bai2_chay_tool.py"))
_bai2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bai2)
chay_tool = _bai2.chay_tool


def vong_lap(client: ClaudeVi, cau_hoi: str, tools: list[dict[str, Any]],
             registry: dict[str, Callable[..., Any]], max_luot: int = 5) -> Message:
    messages: list[dict[str, Any]] = [{"role": "user", "content": cau_hoi}]
    for _ in range(max_luot):
        msg = client.create(messages=messages, tools=tools)
        if msg.stop_reason != "tool_use":
            return msg
        messages.append({"role": "assistant", "content": msg.content})
        messages.append({"role": "user", "content": [
            chay_tool(b, registry) for b in msg.content if b.type == "tool_use"
        ]})
    raise RuntimeError(f"Quá {max_luot} lượt gọi API mà Claude chưa trả lời xong")
