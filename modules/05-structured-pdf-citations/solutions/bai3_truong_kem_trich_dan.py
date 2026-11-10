"""Bài 3 — mỗi trường một dòng, mỗi dòng có trích dẫn. (LỜI GIẢI)"""
from __future__ import annotations

from typing import Any

from anthropic.types import Message


def yeu_cau_truong(tai_lieu: dict[str, Any], truong: list[str]) -> dict[str, Any]:
    if not truong:
        raise ValueError("Cần ít nhất một trường")
    doc = {**tai_lieu, "citations": {"enabled": True}}
    prompt = (f"Trích các trường sau từ tài liệu: {', '.join(truong)}.\n"
              'Trả lời mỗi trường một dòng dạng "ten: gia_tri" và trích nguồn cho từng dòng. '
              "Sau dấu hai chấm chỉ viết giá trị, không giải thích, không đặt trong ngoặc kép.")
    return {"messages": [{"role": "user", "content": [doc, {"type": "text", "text": prompt}]}]}


def tach_truong(msg: Message, truong: list[str]) -> dict[str, dict[str, Any]]:
    if msg.stop_reason != "end_turn":
        raise ValueError(f"Chưa xong: stop_reason={msg.stop_reason}")
    dong: list[dict[str, Any]] = [{"text": "", "trich_dan": []}]
    for block in msg.content:
        if block.type != "text":
            continue
        for k, phan in enumerate(block.text.split("\n")):
            if k > 0:
                dong.append({"text": "", "trich_dan": []})
            dong[-1]["text"] += phan
            if phan:
                dong[-1]["trich_dan"] += [c.cited_text for c in block.citations or []]
    ket_qua: dict[str, dict[str, Any]] = {}
    for d in dong:
        if ":" not in d["text"]:
            continue
        ten, gia_tri = (x.strip() for x in d["text"].split(":", 1))
        if ten in truong and ten not in ket_qua:
            ket_qua[ten] = {"gia_tri": gia_tri, "trich_dan": d["trich_dan"]}
    return ket_qua


def truong_thieu(ket_qua: dict[str, dict[str, Any]], truong: list[str]) -> list[str]:
    return [t for t in truong if t not in ket_qua or not ket_qua[t]["gia_tri"] or not ket_qua[t]["trich_dan"]]
