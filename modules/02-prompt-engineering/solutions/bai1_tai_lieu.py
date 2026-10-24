"""Bài 1 — dựng prompt nhiều tài liệu. (LỜI GIẢI)"""
from __future__ import annotations


def tao_prompt_tai_lieu(tai_lieu: list[tuple[str, str]], cau_hoi: str) -> str:
    if not tai_lieu:
        raise ValueError("Cần ít nhất một tài liệu")
    khoi = "\n".join(
        f'<document index="{i}">\n<source>{nguon}</source>\n<document_content>\n{noi_dung}\n'
        f"</document_content>\n</document>"
        for i, (nguon, noi_dung) in enumerate(tai_lieu, 1)
    )
    return f"<documents>\n{khoi}\n</documents>\n\n<question>\n{cau_hoi}\n</question>"
