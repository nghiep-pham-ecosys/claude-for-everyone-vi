"""Bài 2 — đọc stop_reason và cộng chi phí cả cuộc hội thoại. (LỜI GIẢI)"""
from __future__ import annotations

from anthropic.types import Message

from claude_vi import estimate_cost_usd

HANH_DONG = {
    "end_turn": "dung_ket_qua",
    "stop_sequence": "dung_ket_qua",
    "max_tokens": "tang_max_tokens",
    "model_context_window_exceeded": "rut_gon_lich_su",
    "tool_use": "chay_tool",
    "pause_turn": "gui_lai_nguyen_ven",
    "refusal": "doi_model_hoac_dien_dat_lai",
}


def nen_lam_gi(msg: Message) -> str:
    try:
        return HANH_DONG[msg.stop_reason]
    except KeyError:
        raise ValueError(f"stop_reason chưa biết: {msg.stop_reason!r}") from None


def chi_phi_hoi_thoai(msgs: list[Message]) -> dict[str, float]:
    tong = {"input_tokens": 0, "output_tokens": 0, "thinking_tokens": 0, "usd": 0.0}
    for m in msgs:
        u = m.usage
        tong["input_tokens"] += u.input_tokens
        tong["output_tokens"] += u.output_tokens
        tong["thinking_tokens"] += u.output_tokens_details.thinking_tokens if u.output_tokens_details else 0
        tong["usd"] += estimate_cost_usd(m)
    return tong
