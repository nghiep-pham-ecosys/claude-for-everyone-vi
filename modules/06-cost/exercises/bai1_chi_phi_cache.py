"""Bài 1 — tính chi phí đầy đủ của một response khi có prompt caching và batch.

Giá đọc từ config/models.yaml qua load_models()["models"][model]:
    price_per_mtok        {"input", "output"}
    cache_price_per_mtok  {"write_5m", "write_1h", "read"}
và load_models()["batch_price_multiplier"]. KHÔNG gõ con số giá nào vào code.

chi_phi(msg, batch=False) -> dict USD với các khoá:
    "input"   usage.input_tokens x giá input
    "ghi_5m"  token ghi cache 5 phút x write_5m
    "ghi_1h"  token ghi cache 1 giờ x write_1h
    "doc"     usage.cache_read_input_tokens x read
    "output"  usage.output_tokens x giá output
    "tong"    tổng 5 phần trên
    batch=True: MỌI phần nhân batch_price_multiplier.
    Token ghi 1 giờ lấy ở usage.cache_creation.ephemeral_1h_input_tokens (cache_creation có thể None);
    token ghi 5 phút = cache_creation_input_tokens - token ghi 1 giờ. Trường cache có thể None: coi là 0.
    Model không có trong config, hoặc chưa có price_per_mtok / cache_price_per_mtok: raise ValueError.
    Bỏ qua giá prompt dài (long_context của Haiku 5.5): test dùng prompt dưới 100.000 token.

so_lan_doc_hoa_von(model, ttl) -> int
    Số lần đọc n nhỏ nhất (n >= 1) để 1 lần ghi + n lần đọc RẺ HƠN HẲN (1 + n) lần gửi prefix với giá input.
    ttl là "5m" hoặc "1h"; giá trị khác: raise ValueError.

Chấm:  CHAM=exercises uv run pytest modules/06-cost -q
"""
from __future__ import annotations

from typing import Any

from claude_vi import load_models  # noqa: F401


def chi_phi(msg: Any, batch: bool = False) -> dict[str, float]:
    raise NotImplementedError("TODO: bài 1")


def so_lan_doc_hoa_von(model: str, ttl: str = "5m") -> int:
    raise NotImplementedError("TODO: bài 1")
