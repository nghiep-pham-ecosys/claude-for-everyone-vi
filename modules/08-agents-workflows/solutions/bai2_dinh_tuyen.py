"""Bài 2 — router theo nhãn enum, có nhánh dự phòng. (LỜI GIẢI)"""
from __future__ import annotations

import json
from collections.abc import Callable

from claude_vi import ClaudeVi, text_of

NHAN = ["khac", "quy_trinh", "so_lieu"]
SCHEMA = {"type": "object", "properties": {"nhan": {"type": "string", "enum": NHAN}},
          "required": ["nhan"], "additionalProperties": False}
SYSTEM = (
    "Phân loại câu hỏi của người dùng phòng thí nghiệm. quy_trinh: hỏi cách làm, các bước, mã lỗi thiết bị. "
    "so_lieu: hỏi số đo môi trường hiện tại. khac: mọi câu còn lại."
)


def dinh_tuyen(client: ClaudeVi, cau_hoi: str, xu_ly: dict[str, Callable[[str], str]],
               du_phong: Callable[[str], str]) -> tuple[str, str]:
    msg = client.ask(cau_hoi, system=SYSTEM, output_config={"format": {"type": "json_schema", "schema": SCHEMA}})
    nhan = None
    if msg.stop_reason == "end_turn":
        try:
            nhan = json.loads(text_of(msg)).get("nhan")
        except (json.JSONDecodeError, AttributeError):
            nhan = None
    if nhan in xu_ly:
        return nhan, xu_ly[nhan](cau_hoi)
    return "du_phong", du_phong(cau_hoi)
