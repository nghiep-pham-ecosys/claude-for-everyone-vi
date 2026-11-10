"""Bài 2 — đọc và tự kiểm citations của ba loại tài liệu.

API đảm bảo citation trỏ vào tài liệu bạn gửi. Bài này kiểm lại điều đó bằng code, vì
(1) bạn sẽ lưu và hiển thị vị trí trích dẫn cho người dùng, và (2) response có thể đi qua
nhiều tầng (cache, log, fixture) trước khi tới bạn.

doc_trich_dan(msg, tai_lieu) -> list[TrichDan]
    tai_lieu: danh sách block document ĐÃ GỬI, đúng thứ tự (document_index đếm từ 0 trên mọi document
    của request). Với mỗi citation trong mỗi block text của msg, tạo một TrichDan:
    - khang_dinh = block.text, cited_text, tai_lieu = document_index
    - vi_tri: "ký tự {start}–{end}" | "trang {start}–{end}" | "khối {start}–{end}"
    - hop_le / ly_do theo loại:
        char_location           tài liệu là văn bản thuần và data[start:end] == cited_text
        page_location           tài liệu là PDF; 1 <= start < end <= số_trang + 1 (end không tính);
                                cited_text (đã chuẩn hoá khoảng trắng) có trong text các trang đó
        content_block_location  tài liệu là custom content; 0 <= start < end <= số_khối;
                                cited_text (đã chuẩn hoá) có trong text các khối đó
        document_index ngoài danh sách -> hop_le=False
    - stop_reason khác "end_turn" -> raise ValueError.

trang_pdf(doc) đã viết sẵn.

Chấm:  CHAM=exercises uv run pytest modules/05-structured-pdf-citations -q
"""
from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from typing import Any

from anthropic.types import Message


@dataclass(frozen=True)
class TrichDan:
    khang_dinh: str          # text của block chứa citation
    cited_text: str
    tai_lieu: int            # document_index
    vi_tri: str              # "ký tự 10–42", "trang 1–2", "khối 0–1"
    hop_le: bool
    ly_do: str | None = None


def trang_pdf(doc: dict[str, Any]) -> list[str]:
    """Text từng trang của một document PDF base64 (trang 1 ở chỉ số 0)."""
    from pypdf import PdfReader

    data = base64.b64decode(doc["source"]["data"])
    return [p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages]


def doc_trich_dan(msg: Message, tai_lieu: list[dict[str, Any]]) -> list[TrichDan]:
    raise NotImplementedError("TODO: bài 2")
