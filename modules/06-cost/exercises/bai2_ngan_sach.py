"""Bài 2 — đếm token trước, chỉ gửi khi chi phí tối đa nằm trong ngân sách.

tran_chi_phi(client, params) -> float
    Chi phí TỐI ĐA (USD) của request `params` (dict cho client.create, có thể thiếu "model"/"max_tokens"):
    - model: params["model"] hoặc client.settings.model; max_tokens: params["max_tokens"] hoặc
      client.settings.max_tokens.
    - input: đếm bằng client.count_tokens(...) (bỏ "max_tokens" ra trước: count_tokens không nhận nó),
      tính theo giá input (không giả định cache).
    - KHÔNG sửa dict params của người gọi: chép ra (dict(params)) rồi mới bỏ max_tokens.
    - output: max_tokens x giá output.
    Giá từ load_models()["models"][model]["price_per_mtok"].

goi_trong_ngan_sach(client, params, ngan_sach_usd) -> Message
    tran_chi_phi(...) > ngan_sach_usd: raise VuotNganSach (KHÔNG gọi client.create).
    Ngược lại: trả client.create(**params).
    Mỗi lần gọi hàm này chỉ đếm token ĐÚNG MỘT lần.

Chấm:  CHAM=exercises uv run pytest modules/06-cost -q
"""
from __future__ import annotations

from typing import Any

from claude_vi import ClaudeVi, load_models  # noqa: F401


class VuotNganSach(Exception):
    """Request có thể tốn hơn ngân sách cho phép."""


def tran_chi_phi(client: ClaudeVi, params: dict[str, Any]) -> float:
    raise NotImplementedError("TODO: bài 2")


def goi_trong_ngan_sach(client: ClaudeVi, params: dict[str, Any], ngan_sach_usd: float) -> Any:
    raise NotImplementedError("TODO: bài 2")
