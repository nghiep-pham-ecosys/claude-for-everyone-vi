"""Exercise 3: classify with structured outputs.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
yeu_cau_phan_loai = classification request, doc_phan_loai = read the classification,
van_ban = text, nhan = labels, ly_do = reason.

yeu_cau_phan_loai(van_ban, nhan) -> dict of parameters for client.create(**...)
    - "system": state the task clearly and list the labels.
    - "messages": one user turn, with the text wrapped in <van_ban>...</van_ban>.
    - "output_config": {"format": {"type": "json_schema", "schema": ...}}
      The schema is an object with 2 required fields: "nhan" (string, enum = nhan) and "ly_do" (string).
      Remember additionalProperties: false. Without it the API returns 400 (claude_vi blocks it too).
    - NO prefill, NO temperature.

doc_phan_loai(msg, nhan) -> dict
    - stop_reason other than "end_turn" -> raise ValueError (the JSON may be cut off or not match the schema).
    - json.loads(text_of(msg)).
    - The docs warn that Claude may change the case of an enum value ("Good" instead of "good"):
      match without regard to case and return the exact spelling from `nhan`.
      No label matches -> raise ValueError.

Grade:  CHAM="$PWD/en/modules/02-prompt-engineering/exercises" uv run pytest modules/02-prompt-engineering -q
"""
from __future__ import annotations

import json  # noqa: F401
from typing import Any

from anthropic.types import Message

from claude_vi import text_of  # noqa: F401


def yeu_cau_phan_loai(van_ban: str, nhan: list[str]) -> dict[str, Any]:
    raise NotImplementedError("TODO: exercise 3")


def doc_phan_loai(msg: Message, nhan: list[str]) -> dict[str, str]:
    raise NotImplementedError("TODO: exercise 3")
