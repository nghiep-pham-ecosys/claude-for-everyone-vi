"""Bài 3 — dựng batch đúng luật và gom kết quả theo custom_id. (LỜI GIẢI)"""
from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from claude_vi import estimate_cost_usd, text_of

CUSTOM_ID = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


def tao_requests(viec: dict[str, str]) -> list[dict[str, Any]]:
    if not viec:
        raise ValueError("Batch cần ít nhất một request")
    sai = [ma for ma in viec if not isinstance(ma, str) or not CUSTOM_ID.fullmatch(ma)]
    if sai:
        raise ValueError(f"custom_id không hợp lệ: {sai}")
    return [{"custom_id": ma, "params": {"messages": [{"role": "user", "content": cau}]}}
            for ma, cau in viec.items()]


def gom(ket_qua: Iterable[Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"tra_loi": {}, "loi": {}, "usd": 0.0}
    for r in ket_qua:
        if r.result.type == "succeeded":
            out["tra_loi"][r.custom_id] = text_of(r.result.message)
            out["usd"] += estimate_cost_usd(r.result.message, batch=True)
        else:
            out["loi"][r.custom_id] = r.result.type
    return out
