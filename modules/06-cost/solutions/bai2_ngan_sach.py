"""Bài 2 — đếm token trước, chỉ gửi khi chi phí tối đa nằm trong ngân sách. (LỜI GIẢI)"""
from __future__ import annotations

from typing import Any

from claude_vi import ClaudeVi, load_models


class VuotNganSach(Exception):
    """Request có thể tốn hơn ngân sách cho phép."""


def tran_chi_phi(client: ClaudeVi, params: dict[str, Any]) -> float:
    dem = dict(params)
    max_tokens = dem.pop("max_tokens", client.settings.max_tokens)
    model = dem.setdefault("model", client.settings.model)
    gia = load_models()["models"][model]["price_per_mtok"]
    n = client.count_tokens(**dem).input_tokens
    return (n * gia["input"] + max_tokens * gia["output"]) / 1_000_000


def goi_trong_ngan_sach(client: ClaudeVi, params: dict[str, Any], ngan_sach_usd: float) -> Any:
    tran = tran_chi_phi(client, params)
    if tran > ngan_sach_usd:
        raise VuotNganSach(f"Tối đa ${tran:.6f} > ngân sách ${ngan_sach_usd:.6f}")
    return client.create(**params)
