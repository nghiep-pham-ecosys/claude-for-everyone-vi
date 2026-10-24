"""Bài 2 — khối ví dụ few-shot. (LỜI GIẢI)"""
from __future__ import annotations


def tao_khoi_vi_du(vi_du: list[tuple[str, str]]) -> str:
    if not 3 <= len(vi_du) <= 5:
        raise ValueError(f"Nên có 3–5 ví dụ, nhận {len(vi_du)}")
    nhan = {dau_ra for _, dau_ra in vi_du}
    if len(nhan) < 2:
        raise ValueError("Ví dụ thiếu đa dạng: mọi ví dụ cùng một đầu ra")
    khoi = "\n".join(
        f"<example>\n<input>{dau_vao}</input>\n<output>{dau_ra}</output>\n</example>" for dau_vao, dau_ra in vi_du
    )
    return f"<examples>\n{khoi}\n</examples>"
