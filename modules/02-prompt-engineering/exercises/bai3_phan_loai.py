"""Bài 3 — phân loại bằng structured outputs.

yeu_cau_phan_loai(van_ban, nhan) -> dict tham số cho client.create(**...)
    - "system": nói rõ nhiệm vụ và liệt kê các nhãn.
    - "messages": một lượt user, bọc văn bản trong <van_ban>...</van_ban>.
    - "output_config": {"format": {"type": "json_schema", "schema": ...}}
      schema là object có 2 trường bắt buộc: "nhan" (string, enum = nhan), "ly_do" (string).
      Nhớ additionalProperties: false — thiếu là API trả 400 (claude_vi cũng chặn).
    - KHÔNG prefill, KHÔNG temperature.

doc_phan_loai(msg, nhan) -> dict
    - stop_reason khác "end_turn" -> raise ValueError (JSON có thể bị cắt hoặc không khớp schema).
    - json.loads(text_of(msg)).
    - Docs cảnh báo Claude có thể đổi hoa/thường của giá trị enum ("Tot" thay vì "tot"):
      so khớp không phân biệt hoa thường và trả về đúng cách viết trong `nhan`.
      Không khớp nhãn nào -> raise ValueError.

Chấm:  CHAM=exercises uv run pytest modules/02-prompt-engineering -q
"""
from __future__ import annotations

import json  # noqa: F401
from typing import Any

from anthropic.types import Message

from claude_vi import text_of  # noqa: F401


def yeu_cau_phan_loai(van_ban: str, nhan: list[str]) -> dict[str, Any]:
    raise NotImplementedError("TODO: bài 3")


def doc_phan_loai(msg: Message, nhan: list[str]) -> dict[str, str]:
    raise NotImplementedError("TODO: bài 3")
