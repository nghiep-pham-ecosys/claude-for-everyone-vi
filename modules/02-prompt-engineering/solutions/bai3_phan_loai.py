"""Bài 3 — phân loại bằng structured outputs. (LỜI GIẢI)"""
from __future__ import annotations

import json
from typing import Any

from anthropic.types import Message

from claude_vi import text_of


def yeu_cau_phan_loai(van_ban: str, nhan: list[str]) -> dict[str, Any]:
    schema = {
        "type": "object",
        "properties": {
            "nhan": {"type": "string", "enum": nhan},
            "ly_do": {"type": "string"},
        },
        "required": ["nhan", "ly_do"],
        "additionalProperties": False,
    }
    return {
        "system": f"Bạn phân loại văn bản vào đúng một nhãn trong: {', '.join(nhan)}.",
        "messages": [{"role": "user", "content": f"<van_ban>{van_ban}</van_ban>"}],
        "output_config": {"format": {"type": "json_schema", "schema": schema}},
    }


def doc_phan_loai(msg: Message, nhan: list[str]) -> dict[str, str]:
    if msg.stop_reason != "end_turn":
        raise ValueError(f"Không dùng được kết quả: stop_reason={msg.stop_reason}")
    data = json.loads(text_of(msg))
    theo_chu_thuong = {n.lower(): n for n in nhan}
    try:
        data["nhan"] = theo_chu_thuong[data["nhan"].lower()]
    except KeyError:
        raise ValueError(f"Nhãn lạ: {data['nhan']!r}") from None
    return data
