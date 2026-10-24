"""Bài 2 — khối ví dụ few-shot.

tao_khoi_vi_du(vi_du) -> str
    vi_du: list (dau_vao, dau_ra).
    - Ít hơn 3 hoặc nhiều hơn 5 ví dụ -> raise ValueError (docs khuyên 3–5).
    - Mọi ví dụ cùng một dau_ra -> raise ValueError (thiếu đa dạng: Claude sẽ học nhầm "luôn trả X").
    - Kết quả:

    <examples>
    <example>
    <input>dau_vao</input>
    <output>dau_ra</output>
    </example>
    ...
    </examples>

Chấm:  CHAM=exercises uv run pytest modules/02-prompt-engineering -q
"""
from __future__ import annotations


def tao_khoi_vi_du(vi_du: list[tuple[str, str]]) -> str:
    raise NotImplementedError("TODO: bài 2")
