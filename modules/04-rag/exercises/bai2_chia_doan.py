"""Bài 2 — chia tài liệu thành đoạn và thêm ngữ cảnh.

chia_doan(tai_lieu, max_ky_tu=400) -> list[Doan]
    Tài liệu là markdown: một dòng "# Tiêu đề", các dòng "## Mục", đoạn văn cách nhau bằng dòng trống.
    - Phần trước mục "##" đầu tiên là một phần có muc = "".
    - Trong mỗi mục, gom các đoạn văn liên tiếp (nối bằng "\\n\\n") miễn tổng độ dài còn ≤ max_ky_tu.
      Thêm một đoạn văn nữa mà vượt thì đóng Doan hiện tại, mở Doan mới. Một đoạn văn dài hơn max_ky_tu
      vẫn đứng một mình, KHÔNG cắt giữa câu.
    - Không gom qua ranh giới mục. Mục không có chữ thì không sinh Doan.
    - id = "{tai_lieu.ten}#{n}", n đếm từ 1 theo thứ tự trong tài liệu. Dòng "#"/"##" không nằm trong noi_dung.

them_ngu_canh(doan) -> str
    "Tài liệu: {tieu_de}. Mục: {muc}.\\n{noi_dung}"; muc rỗng thì bỏ " Mục: ...".
    Đây là cách thêm ngữ cảnh miễn phí: chép tiêu đề và tên mục vào đầu đoạn trước khi lập chỉ mục.

yeu_cau_ngu_canh(tai_lieu, doan) -> dict tham số cho client.create(**...)
    Nhờ Claude viết 1–2 câu ngữ cảnh cho đoạn (contextual retrieval):
    - một lượt user: cả tài liệu trong <document>...</document> TRƯỚC, rồi đoạn trong <chunk>...</chunk>,
      rồi yêu cầu chỉ trả câu ngữ cảnh;
    - "max_tokens" ≤ 256 và "output_config": {"effort": "low"}: việc ngắn, làm cho hàng nghìn đoạn.

Chấm:  CHAM=exercises uv run pytest modules/04-rag -q
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TaiLieu:
    ten: str          # tên file không đuôi, ví dụ "01_hieu_chuan_ph"
    noi_dung: str     # markdown đầy đủ


@dataclass(frozen=True)
class Doan:
    id: str           # "{ten}#{số thứ tự từ 1}"
    tieu_de: str      # dòng "# ..." của tài liệu
    muc: str          # dòng "## ..." chứa đoạn; "" nếu đoạn ở trước mục đầu tiên
    noi_dung: str


def chia_doan(tai_lieu: TaiLieu, max_ky_tu: int = 400) -> list[Doan]:
    raise NotImplementedError("TODO: bài 2")


def them_ngu_canh(doan: Doan) -> str:
    raise NotImplementedError("TODO: bài 2")


def yeu_cau_ngu_canh(tai_lieu: TaiLieu, doan: Doan) -> dict[str, Any]:
    raise NotImplementedError("TODO: bài 2")
