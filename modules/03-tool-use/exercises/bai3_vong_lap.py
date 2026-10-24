"""Bài 3 — vòng lặp tool hoàn chỉnh.

vong_lap(client, cau_hoi, tools, registry, max_luot=5) -> Message cuối cùng
    - Bắt đầu với messages = [lượt user cau_hoi].
    - Mỗi lượt: client.create(messages=..., tools=tools).
      stop_reason khác "tool_use" -> trả về message đó.
    - Ngược lại: nối lượt assistant với msg.content NGUYÊN VẸN (mock trả 400 nếu bạn bỏ block thinking),
      rồi MỘT lượt user chứa tool_result cho MỌI tool_use (dùng chay_tool ở bài 2), giữ đúng thứ tự.
    - max_luot là số lần gọi API tối đa. Hết lượt mà vẫn "tool_use" -> raise RuntimeError.

Chấm:  CHAM=exercises uv run pytest modules/03-tool-use -q
"""
from __future__ import annotations

import importlib.util
from collections.abc import Callable
from pathlib import Path
from typing import Any

from anthropic.types import Message

from claude_vi import ClaudeVi

# Dùng lại chay_tool từ bài 2 của chính bạn
_spec = importlib.util.spec_from_file_location("bai2_cua_ban", Path(__file__).with_name("bai2_chay_tool.py"))
_bai2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bai2)
chay_tool = _bai2.chay_tool


def vong_lap(client: ClaudeVi, cau_hoi: str, tools: list[dict[str, Any]],
             registry: dict[str, Callable[..., Any]], max_luot: int = 5) -> Message:
    raise NotImplementedError("TODO: bài 3")
