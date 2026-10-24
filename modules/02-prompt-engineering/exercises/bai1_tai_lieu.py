"""Bài 1 — dựng prompt nhiều tài liệu.

tao_prompt_tai_lieu(tai_lieu, cau_hoi) -> str
    tai_lieu: list (nguon, noi_dung). Rỗng -> raise ValueError.
    Kết quả có dạng (đúng thứ tự, index đếm từ 1):

    <documents>
    <document index="1">
    <source>nguon</source>
    <document_content>
    noi_dung
    </document_content>
    </document>
    ... (các tài liệu tiếp theo)
    </documents>

    <question>
    cau_hoi
    </question>

Vì sao: tài liệu dài đặt TRƯỚC, câu hỏi đặt CUỐI cho kết quả tốt hơn; thẻ XML tách rõ dữ liệu và câu hỏi.

Chấm:  CHAM=exercises uv run pytest modules/02-prompt-engineering -q
"""
from __future__ import annotations


def tao_prompt_tai_lieu(tai_lieu: list[tuple[str, str]], cau_hoi: str) -> str:
    raise NotImplementedError("TODO: bài 1")
