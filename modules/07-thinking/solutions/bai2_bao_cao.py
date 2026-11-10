"""Bài 2 — đọc thinking và chẩn đoán response. (LỜI GIẢI)"""
from __future__ import annotations

from dataclasses import dataclass

from anthropic.types import Message
from claude_vi import text_of


@dataclass(frozen=True)
class BaoCao:
    khoi_thinking: int
    khoi_redacted: int
    tom_tat: str
    thinking_tokens: int
    text_tokens: int
    ty_le_thinking: float


def bao_cao(msg: Message) -> BaoCao:
    thinking = [b for b in msg.content if b.type == "thinking"]
    redacted = [b for b in msg.content if b.type == "redacted_thinking"]
    u = msg.usage
    t = (u.output_tokens_details.thinking_tokens if u.output_tokens_details else None) or 0
    return BaoCao(
        khoi_thinking=len(thinking),
        khoi_redacted=len(redacted),
        tom_tat="\n".join(b.thinking for b in thinking if b.thinking),
        thinking_tokens=t,
        text_tokens=u.output_tokens - t,
        ty_le_thinking=round(t / u.output_tokens, 2) if u.output_tokens else 0.0,
    )


def chan_doan(msg: Message) -> str:
    if msg.stop_reason == "refusal":
        return "tu_choi"
    if msg.stop_reason == "model_context_window_exceeded":
        return "het_context"
    if msg.stop_reason == "max_tokens":
        return "thinking_dung_het_max_tokens" if not text_of(msg).strip() else "bi_cat_ngang"
    return "ok"
