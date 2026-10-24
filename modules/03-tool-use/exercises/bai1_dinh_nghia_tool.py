"""Bài 1 — định nghĩa tool strict.

tao_tool(ten, mo_ta, thuoc_tinh, bat_buoc) -> dict định nghĩa tool
    - ten phải khớp ^[a-zA-Z0-9_-]{1,128}$ (không dấu tiếng Việt, không khoảng trắng) -> sai thì ValueError.
    - mo_ta: docs nói mô tả chi tiết là yếu tố QUAN TRỌNG NHẤT, nên viết ít nhất 3–4 câu.
      Ở đây: ít hơn 3 dấu chấm -> ValueError.
    - Mọi tên trong bat_buoc phải có trong thuoc_tinh -> nếu không, ValueError.
    - Kết quả:
        {"name": ten, "description": mo_ta, "strict": True,
         "input_schema": {"type": "object", "properties": thuoc_tinh,
                          "required": bat_buoc, "additionalProperties": False}}

Chấm:  CHAM=exercises uv run pytest modules/03-tool-use -q
"""
from __future__ import annotations

from typing import Any


def tao_tool(ten: str, mo_ta: str, thuoc_tinh: dict[str, dict[str, Any]], bat_buoc: list[str]) -> dict[str, Any]:
    raise NotImplementedError("TODO: bài 1")
