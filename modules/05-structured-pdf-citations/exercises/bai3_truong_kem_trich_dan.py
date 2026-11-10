"""Bài 3 — mỗi trường một dòng, mỗi dòng có trích dẫn.

Citations không dùng chung được với structured outputs. Cách docs gợi ý: xin mỗi trường một
dòng "ten: gia_tri", trích nguồn từng dòng, rồi tự tách.

yeu_cau_truong(tai_lieu, truong) -> dict tham số cho client.create(**...)
    - Bật citations trên document (citations.enabled = True), đặt document TRƯỚC câu hỏi.
    - Prompt nêu đủ tên các trường, yêu cầu mỗi trường một dòng "ten: gia_tri", trích nguồn từng dòng,
      sau dấu hai chấm chỉ viết giá trị.
    - KHÔNG có output_config (sẽ 400), KHÔNG viết "chỉ trả JSON" (request chạy nhưng gần như mất trích dẫn).
    - truong rỗng -> raise ValueError.

tach_truong(msg, truong) -> {ten: {"gia_tri": str, "trich_dan": [cited_text, ...]}}
    Theo thuật toán của docs:
    1. Đọc các block text theo thứ tự, nối text vào dòng hiện tại; gặp "\\n" thì sang dòng mới.
    2. Gắn citations của một block vào MỌI dòng chứa một phần text của block đó.
    3. Bỏ dòng không có dấu hai chấm. Tách ở dấu hai chấm ĐẦU TIÊN (giá trị "08:20" vẫn giữ nguyên),
       bỏ khoảng trắng hai đầu. Bỏ dòng có tên không thuộc `truong`. Tên lặp lại thì giữ lần đầu.
    - stop_reason khác "end_turn" -> raise ValueError.

truong_thieu(ket_qua, truong) -> list[str]
    Các trường (theo thứ tự trong `truong`) không có, có giá trị rỗng, hoặc không có trích dẫn nào.
    API không đảm bảo trường nào cũng có giá trị và trích dẫn — phải tự kiểm.

Chấm:  CHAM=exercises uv run pytest modules/05-structured-pdf-citations -q
"""
from __future__ import annotations

from typing import Any

from anthropic.types import Message


def yeu_cau_truong(tai_lieu: dict[str, Any], truong: list[str]) -> dict[str, Any]:
    raise NotImplementedError("TODO: bài 3")


def tach_truong(msg: Message, truong: list[str]) -> dict[str, dict[str, Any]]:
    raise NotImplementedError("TODO: bài 3")


def truong_thieu(ket_qua: dict[str, dict[str, Any]], truong: list[str]) -> list[str]:
    raise NotImplementedError("TODO: bài 3")
