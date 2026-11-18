"""Bài 1 — chuỗi hai bước có cổng kiểm.

kiem_cong(du_lieu) -> None nếu qua cổng, ngược lại là một chuỗi nói lý do trượt. Kiểm theo thứ tự:
    - du_lieu là dict và có đủ ba trường dai_luong, gia_tri, don_vi;
    - dai_luong có trong GIOI_HAN;
    - gia_tri là số (int hoặc float; bool KHÔNG tính là số);
    - don_vi đúng đơn vị trong GIOI_HAN;
    - lo <= gia_tri <= hi.
    Cổng là code, không gọi Claude.

chuoi_hai_buoc(client, van_ban) -> {"ok", "ly_do", "phep_do", "tom_tat"}
    - Bước 1: MỘT lời gọi client.ask(...) có van_ban, với
      output_config={"format": {"type": "json_schema", "schema": SCHEMA}}.
    - stop_reason khác "end_turn" hoặc JSON hỏng -> ok False, ly_do khác rỗng, KHÔNG gọi bước 2.
    - Cổng trượt -> ok False, ly_do là lý do của kiem_cong, phep_do là dict đã trích, KHÔNG gọi bước 2.
    - Cổng qua -> bước 2: một lời gọi viết câu tóm tắt; ok True, ly_do None, tom_tat là text_of của bước 2.
    Test đếm số lời gọi: cổng trượt mà vẫn gọi bước 2 là trượt bài.

Chấm:  CHAM=exercises uv run pytest modules/08-agents-workflows -q
"""
from __future__ import annotations

from typing import Any

from claude_vi import ClaudeVi

# Khoảng hợp lệ và đơn vị của từng đại lượng (số liệu hư cấu)
GIOI_HAN = {
    "pH": (0.0, 14.0, ""),
    "nhiet_do_c": (-10.0, 60.0, "°C"),
    "do_doc_dien_cuc": (80.0, 120.0, "%"),
}
SCHEMA = {
    "type": "object",
    "properties": {
        "dai_luong": {"type": "string", "enum": list(GIOI_HAN)},
        "gia_tri": {"type": "number"},
        "don_vi": {"type": "string"},
    },
    "required": ["dai_luong", "gia_tri", "don_vi"],
    "additionalProperties": False,
}


def kiem_cong(du_lieu: Any) -> str | None:
    raise NotImplementedError("TODO: bài 1, cổng kiểm")


def chuoi_hai_buoc(client: ClaudeVi, van_ban: str) -> dict[str, Any]:
    raise NotImplementedError("TODO: bài 1, chuỗi hai bước")
