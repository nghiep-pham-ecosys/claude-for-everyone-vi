"""Bài 2 — đọc stop_reason và cộng chi phí cả cuộc hội thoại.

nen_lam_gi(msg) trả về MỘT trong các chuỗi sau theo msg.stop_reason:
    end_turn, stop_sequence          -> "dung_ket_qua"
    max_tokens                       -> "tang_max_tokens"
    model_context_window_exceeded    -> "rut_gon_lich_su"
    tool_use                         -> "chay_tool"
    pause_turn                       -> "gui_lai_nguyen_ven"
    refusal                          -> "doi_model_hoac_dien_dat_lai"
    giá trị khác                     -> raise ValueError (đừng coi lý do lạ là thành công)

chi_phi_hoi_thoai(msgs) trả dict có 4 khoá:
    input_tokens, output_tokens, thinking_tokens (từ usage.output_tokens_details, có thể None), usd
    usd = tổng estimate_cost_usd(m).

Chấm:  CHAM=exercises uv run pytest modules/01-messages-api -q
"""
from __future__ import annotations

from anthropic.types import Message

from claude_vi import estimate_cost_usd  # noqa: F401


def nen_lam_gi(msg: Message) -> str:
    raise NotImplementedError("TODO: bài 2")


def chi_phi_hoi_thoai(msgs: list[Message]) -> dict[str, float]:
    raise NotImplementedError("TODO: bài 2")
