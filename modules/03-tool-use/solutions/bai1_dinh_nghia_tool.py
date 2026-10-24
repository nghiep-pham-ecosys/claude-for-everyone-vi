"""Bài 1 — định nghĩa tool strict. (LỜI GIẢI)"""
from __future__ import annotations

import re
from typing import Any

TEN_HOP_LE = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")


def tao_tool(ten: str, mo_ta: str, thuoc_tinh: dict[str, dict[str, Any]], bat_buoc: list[str]) -> dict[str, Any]:
    if not TEN_HOP_LE.match(ten):
        raise ValueError(f"Tên tool không hợp lệ: {ten!r}")
    if mo_ta.count(".") < 3:
        raise ValueError("Mô tả quá ngắn: viết ít nhất 3 câu (làm gì, khi nào dùng, trả về gì)")
    thieu = set(bat_buoc) - set(thuoc_tinh)
    if thieu:
        raise ValueError(f"Trường bắt buộc không có trong thuoc_tinh: {sorted(thieu)}")
    return {
        "name": ten,
        "description": mo_ta,
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": thuoc_tinh,
            "required": bat_buoc,
            "additionalProperties": False,
        },
    }
