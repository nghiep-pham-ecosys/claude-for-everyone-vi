"""Bài 1 — tính chi phí đầy đủ của một response khi có prompt caching và batch. (LỜI GIẢI)"""
from __future__ import annotations

from typing import Any

from claude_vi import load_models

MTOK = 1_000_000


def _entry(model: str) -> dict[str, Any]:
    entry = load_models()["models"].get(model)
    if not entry or not entry.get("price_per_mtok") or not entry.get("cache_price_per_mtok"):
        raise ValueError(f"Model '{model}' chưa có giá trong config/models.yaml")
    return entry


def chi_phi(msg: Any, batch: bool = False) -> dict[str, float]:
    entry = _entry(msg.model)
    gia, cache = entry["price_per_mtok"], entry["cache_price_per_mtok"]
    u = msg.usage
    ghi_1h = u.cache_creation.ephemeral_1h_input_tokens if u.cache_creation else 0
    ghi_5m = (u.cache_creation_input_tokens or 0) - ghi_1h
    he_so = load_models()["batch_price_multiplier"] if batch else 1.0
    out = {
        "input": u.input_tokens * gia["input"],
        "ghi_5m": ghi_5m * cache["write_5m"],
        "ghi_1h": ghi_1h * cache["write_1h"],
        "doc": (u.cache_read_input_tokens or 0) * cache["read"],
        "output": u.output_tokens * gia["output"],
    }
    out = {k: v / MTOK * he_so for k, v in out.items()}
    out["tong"] = sum(out.values())
    return out


def so_lan_doc_hoa_von(model: str, ttl: str = "5m") -> int:
    if ttl not in ("5m", "1h"):
        raise ValueError('ttl phải là "5m" hoặc "1h"')
    entry = _entry(model)
    vao, cache = entry["price_per_mtok"]["input"], entry["cache_price_per_mtok"]
    n = 1
    while cache[f"write_{ttl}"] + n * cache["read"] >= (1 + n) * vao:
        n += 1
    return n
