"""Bài 2 — đọc và tự kiểm citations của ba loại tài liệu. (LỜI GIẢI)"""
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


def _chuan_hoa(text: str) -> str:
    return " ".join(text.split())


def trang_pdf(doc: dict[str, Any]) -> list[str]:
    """Text từng trang của một document PDF base64 (trang 1 ở chỉ số 0)."""
    from pypdf import PdfReader

    data = base64.b64decode(doc["source"]["data"])
    return [p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages]


def _kiem(c: Any, doc: dict[str, Any]) -> tuple[str, str | None]:
    source = doc["source"]
    if c.type == "char_location":
        vi_tri = f"ký tự {c.start_char_index}–{c.end_char_index}"
        if source.get("type") != "text":
            return vi_tri, "char_location nhưng tài liệu không phải văn bản thuần"
        if source["data"][c.start_char_index:c.end_char_index] != c.cited_text:
            return vi_tri, "đoạn văn bản ở vị trí này khác cited_text"
        return vi_tri, None
    if c.type == "page_location":
        vi_tri = f"trang {c.start_page_number}–{c.end_page_number}"
        if source.get("media_type") != "application/pdf":
            return vi_tri, "page_location nhưng tài liệu không phải PDF"
        trang = trang_pdf(doc)
        if not 1 <= c.start_page_number < c.end_page_number <= len(trang) + 1:
            return vi_tri, f"trang ngoài khoảng 1–{len(trang)}"
        vung = _chuan_hoa(" ".join(trang[c.start_page_number - 1:c.end_page_number - 1]))
        return vi_tri, None if _chuan_hoa(c.cited_text) in vung else "không tìm thấy cited_text ở các trang này"
    if c.type == "content_block_location":
        vi_tri = f"khối {c.start_block_index}–{c.end_block_index}"
        if source.get("type") != "content":
            return vi_tri, "content_block_location nhưng tài liệu không phải custom content"
        khoi = source["content"]
        if not 0 <= c.start_block_index < c.end_block_index <= len(khoi):
            return vi_tri, f"khối ngoài khoảng 0–{len(khoi) - 1}"
        vung = _chuan_hoa(" ".join(b["text"] for b in khoi[c.start_block_index:c.end_block_index]))
        return vi_tri, None if _chuan_hoa(c.cited_text) in vung else "không tìm thấy cited_text ở các khối này"
    return "?", f"loại citation chưa hỗ trợ: {c.type}"


def doc_trich_dan(msg: Message, tai_lieu: list[dict[str, Any]]) -> list[TrichDan]:
    if msg.stop_reason != "end_turn":
        raise ValueError(f"Lượt trích dẫn chưa xong: stop_reason={msg.stop_reason}")
    ket_qua = []
    for block in msg.content:
        if block.type != "text":
            continue
        for c in block.citations or []:
            if not 0 <= c.document_index < len(tai_lieu):
                vi_tri, ly_do = "?", f"document_index {c.document_index} không tồn tại"
            else:
                vi_tri, ly_do = _kiem(c, tai_lieu[c.document_index])
            ket_qua.append(TrichDan(block.text, c.cited_text, c.document_index, vi_tri, ly_do is None, ly_do))
    return ket_qua
