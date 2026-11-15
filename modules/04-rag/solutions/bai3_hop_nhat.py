"""Bài 3 — hợp nhất xếp hạng (RRF), đóng gói search_result, đọc trích dẫn. (LỜI GIẢI)"""
from __future__ import annotations

from typing import Any

from anthropic.types import Message


def hop_nhat_rrf(*xep_hang: list[str], k: int = 60) -> list[tuple[str, float]]:
    diem: dict[str, float] = {}
    for ds in xep_hang:
        for hang, id_ in enumerate(ds, 1):
            diem[id_] = diem.get(id_, 0.0) + 1 / (k + hang)
    thu_tu = list(diem)                                   # dict giữ thứ tự xuất hiện đầu tiên
    return sorted(diem.items(), key=lambda x: (-x[1], thu_tu.index(x[0])))


def khoi_ket_qua(doan: list[Any], citations: bool = True) -> list[dict[str, Any]]:
    ket_qua = []
    for d in doan:
        khoi = [{"type": "text", "text": dong.strip()} for dong in d.noi_dung.split("\n") if dong.strip()]
        ket_qua.append({
            "type": "search_result",
            "source": f"kb://so-tay/{d.id}",
            "title": f"{d.tieu_de} — {d.muc}" if d.muc else d.tieu_de,
            "content": khoi,
            "citations": {"enabled": citations},
        })
    return ket_qua


def nguon_trich_dan(msg: Message) -> list[dict[str, str]]:
    if msg.stop_reason != "end_turn":
        raise ValueError(f"Chưa xong: stop_reason={msg.stop_reason}")
    ket_qua, da_co = [], set()
    for b in msg.content:
        if b.type != "text":
            continue
        for c in b.citations or []:
            if c.type != "search_result_location":
                continue
            khoa = (c.source, c.cited_text)
            if khoa not in da_co:
                da_co.add(khoa)
                ket_qua.append({"source": c.source, "title": c.title or "", "cited_text": c.cited_text})
    return ket_qua
