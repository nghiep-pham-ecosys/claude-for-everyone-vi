"""Bài 3 — hợp nhất xếp hạng (RRF), đóng gói search_result, đọc trích dẫn.

hop_nhat_rrf(*xep_hang, k=60) -> list[(id, điểm)]
    Reciprocal Rank Fusion: mỗi xep_hang là danh sách id, tốt nhất đứng đầu (hạng 1).
    điểm(id) = tổng trên các danh sách chứa id của 1 / (k + hạng). Sắp điểm giảm dần; bằng điểm thì id
    xuất hiện trước (duyệt danh sách thứ nhất, rồi thứ hai...) đứng trước.
    RRF chỉ dùng thứ hạng, không dùng điểm gốc, nên ghép được BM25 với embedding dù thang điểm khác nhau.

khoi_ket_qua(doan, citations=True) -> list[dict]
    Mỗi Doan thành một block:
        {"type": "search_result", "source": "kb://so-tay/{id}", "title": ..., "content": [...],
         "citations": {"enabled": citations}}
    - title: "{tieu_de} — {muc}", hoặc chỉ tieu_de nếu muc rỗng.
    - content: mỗi dòng không rỗng của noi_dung là một block {"type": "text", "text": dòng đã strip}.
      Claude trích nguyên block, nên block nhỏ cho trích dẫn sát hơn.

nguon_trich_dan(msg) -> list[{"source", "title", "cited_text"}]
    Citation loại "search_result_location" trong các block text, theo thứ tự, bỏ trùng (source, cited_text).
    title None thì ghi "". stop_reason khác "end_turn" -> raise ValueError.

Chấm:  CHAM=exercises uv run pytest modules/04-rag -q
"""
from __future__ import annotations

from typing import Any

from anthropic.types import Message


def hop_nhat_rrf(*xep_hang: list[str], k: int = 60) -> list[tuple[str, float]]:
    raise NotImplementedError("TODO: bài 3")


def khoi_ket_qua(doan: list[Any], citations: bool = True) -> list[dict[str, Any]]:
    raise NotImplementedError("TODO: bài 3")


def nguon_trich_dan(msg: Message) -> list[dict[str, str]]:
    raise NotImplementedError("TODO: bài 3")
