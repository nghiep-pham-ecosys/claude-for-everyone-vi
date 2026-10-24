"""Capstone c2 — ba hàm cốt lõi của pipeline. Đọc README.md của capstone trước.

doc_trich_dan(msg) -> list[TrichDan]
    msg: response của lượt 1 (document PDF có citations.enabled).
    - stop_reason khác "end_turn" -> ValueError.
    - Duyệt các block text; với mỗi citation có type "page_location":
      TrichDan(id="C1", "C2", ... theo thứ tự xuất hiện, trang=start_page_number, van_ban=cited_text đã strip()).
    - Bỏ trùng: cùng (trang, van_ban) chỉ giữ lần đầu (id không nhảy số).
    - Bỏ qua block không phải text và citation không phải page_location.

yeu_cau_cau_truc(trich_dan) -> dict tham số cho client.create(**...)  (lượt 2, structured outputs)
    - Danh sách rỗng -> ValueError.
    - KHÔNG gửi lại PDF ở lượt này (citations + structured outputs = 400).
    - "messages": một lượt user liệt kê từng trích dẫn dạng <trich_dan id="C1" trang="1">van_ban</trich_dan>.
    - "system": nói rõ chỉ dùng con số có trong trích dẫn.
    - "output_config.format": schema object {"phep_do": array}, mỗi phần tử là object có ĐỦ 6 trường bắt buộc
      TRUONG = nguon (string, enum = các id trích dẫn), thi_nghiem, mau, dai_luong (string),
      gia_tri (number), don_vi (string). Mọi object có additionalProperties: false.
      Vì sao enum cho nguon: API đảm bảo model chỉ trỏ tới trích dẫn có thật.

kiem_chung(phep_do, trich_dan, trang_pdf) -> list[dict]
    Với mỗi dòng trong phep_do, trả về dòng đó + 4 khoá: trang, trich_dan, da_kiem_chung (bool), ly_do (str | None).
    Kiểm theo thứ tự, dừng ở lỗi đầu tiên:
      1. nguon không có trong trich_dan -> ly_do chứa "không tồn tại", trang/trich_dan = None.
      2. van_ban của trích dẫn không nằm trong text của trang đó (trang_pdf[trang - 1]), so sau khi gộp khoảng trắng
         -> ly_do chứa "không tìm thấy".
      3. gia_tri không bằng con số nào trong van_ban (hiểu cả "7,2" lẫn "7.2") -> ly_do chứa "không có trong trích dẫn".
    Hợp lệ -> da_kiem_chung True, ly_do None.

Chấm:  CHAM=exercises uv run pytest capstones/c2-trich-xuat-pdf -q
"""
from __future__ import annotations

import re  # noqa: F401
from dataclasses import dataclass
from typing import Any

from anthropic.types import Message


@dataclass(frozen=True)
class TrichDan:
    """Một trích dẫn lấy từ citations của API: id do ta đặt, trang và văn bản do API trả về."""
    id: str
    trang: int
    van_ban: str

TRUONG = ["nguon", "thi_nghiem", "mau", "dai_luong", "gia_tri", "don_vi"]


def doc_trich_dan(msg: Message) -> list[TrichDan]:
    raise NotImplementedError("TODO: capstone c2")


def yeu_cau_cau_truc(trich_dan: list[TrichDan]) -> dict[str, Any]:
    raise NotImplementedError("TODO: capstone c2")


def kiem_chung(phep_do: list[dict[str, Any]], trich_dan: list[TrichDan], trang_pdf: list[str]) -> list[dict[str, Any]]:
    raise NotImplementedError("TODO: capstone c2")
