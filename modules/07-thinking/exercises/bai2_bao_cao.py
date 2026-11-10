"""Bài 2 — đọc thinking và chẩn đoán response.

bao_cao(msg) -> BaoCao
    - khoi_thinking:   số block type "thinking"
    - khoi_redacted:   số block type "redacted_thinking" (bị che vì an toàn, không có text)
    - tom_tat:         text của các block thinking KHÔNG rỗng, nối bằng "\\n" ("" nếu display omitted)
    - thinking_tokens: usage.output_tokens_details.thinking_tokens; output_tokens_details hoặc giá trị
                       có thể là None -> coi là 0
    - text_tokens:     output_tokens - thinking_tokens
    - ty_le_thinking:  thinking_tokens / output_tokens, làm tròn 2 chữ số; output_tokens = 0 -> 0.0

chan_doan(msg) -> str, một trong:
    "tu_choi"                       stop_reason == "refusal"
    "het_context"                   stop_reason == "model_context_window_exceeded"
    "thinking_dung_het_max_tokens"  stop_reason == "max_tokens" và text_of(msg) rỗng (sau strip)
    "bi_cat_ngang"                  stop_reason == "max_tokens" và có text
    "ok"                            các trường hợp còn lại

Chấm:  CHAM=exercises uv run pytest modules/07-thinking -q
"""
from __future__ import annotations

from dataclasses import dataclass

from anthropic.types import Message
from claude_vi import text_of  # noqa: F401


@dataclass(frozen=True)
class BaoCao:
    khoi_thinking: int
    khoi_redacted: int
    tom_tat: str
    thinking_tokens: int
    text_tokens: int
    ty_le_thinking: float


def bao_cao(msg: Message) -> BaoCao:
    raise NotImplementedError("TODO: bài 2")


def chan_doan(msg: Message) -> str:
    raise NotImplementedError("TODO: bài 2")
