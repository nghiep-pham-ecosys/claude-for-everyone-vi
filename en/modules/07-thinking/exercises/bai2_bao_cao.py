"""Exercise 2: read the thinking and diagnose the response.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
bao_cao / BaoCao = report, chan_doan = diagnose, khoi = block, tom_tat = summary, ty_le = ratio.

bao_cao(msg) -> BaoCao
    - khoi_thinking:   the number of blocks of type "thinking"
    - khoi_redacted:   the number of blocks of type "redacted_thinking" (hidden for safety, no text)
    - tom_tat:         the text of the NON-empty thinking blocks, joined with "\\n" ("" with display omitted)
    - thinking_tokens: usage.output_tokens_details.thinking_tokens; output_tokens_details or the value
                       can be None -> treat it as 0
    - text_tokens:     output_tokens - thinking_tokens
    - ty_le_thinking:  thinking_tokens / output_tokens, rounded to 2 decimals; output_tokens = 0 -> 0.0

chan_doan(msg) -> str, one of these values (they stay in Vietnamese):
    "tu_choi"                       (refused)          stop_reason == "refusal"
    "het_context"                   (out of context)   stop_reason == "model_context_window_exceeded"
    "thinking_dung_het_max_tokens"  (thinking used up max_tokens)
                                    stop_reason == "max_tokens" and text_of(msg) is empty (after strip)
    "bi_cat_ngang"                  (cut off midway)   stop_reason == "max_tokens" and there is text
    "ok"                            every other case

Grade:  CHAM="$PWD/en/modules/07-thinking/exercises" uv run pytest modules/07-thinking -q
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
    raise NotImplementedError("TODO: exercise 2")


def chan_doan(msg: Message) -> str:
    raise NotImplementedError("TODO: exercise 2")
