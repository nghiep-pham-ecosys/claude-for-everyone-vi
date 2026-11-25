"""Exercise 1: a water monitoring form with Pydantic + structured outputs.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
phieu_nuoc = water form, ma_mau = sample code, do_mg_l = dissolved oxygen in mg/L, danh_gia = verdict,
dat / khong_dat = pass / fail, ghi_chu = note, yeu_cau_phieu = form request, van_ban = text, doc_phieu = read form.

class PhieuNuoc(BaseModel): write these fields:
    - ma_mau: str
    - ph: float, between 0 and 14             (Field(ge=..., le=...))
    - do_mg_l: float, not negative            (dissolved oxygen, mg/L)
    - danh_gia: only "dat" or "khong_dat"     (Literal)
    - ghi_chu: str or None, default None      (the only optional field)

yeu_cau_phieu(van_ban) -> a dict of parameters for client.create(**...)
    - "system": state the task clearly, and why only numbers found in the text may be used.
    - "messages": one user turn, with the text wrapped in <van_ban>...</van_ban>.
    - "output_config": {"format": {"type": "json_schema", "schema": transform_schema(PhieuNuoc)}}
      Sending PhieuNuoc.model_json_schema() as it is fails with 400 ("minimum" is there,
      additionalProperties is missing).

doc_phieu(msg) -> PhieuNuoc
    - stop_reason other than "end_turn" -> raise ValueError.
    - Claude can change the case of an enum value ("Dat"): lower-case danh_gia before you check it.
    - Check with PhieuNuoc.model_validate(...): pH 15 still "matches the schema" but breaks your constraint,
      and it must be caught here (pydantic.ValidationError is a ValueError).

Grade:  CHAM="$PWD/en/modules/05-structured-pdf-citations/exercises" uv run pytest modules/05-structured-pdf-citations -q
"""
from __future__ import annotations

import json  # noqa: F401
from typing import Any, Literal  # noqa: F401

from anthropic import transform_schema  # noqa: F401
from anthropic.types import Message
from claude_vi import text_of  # noqa: F401
from pydantic import BaseModel, Field  # noqa: F401


class PhieuNuoc(BaseModel):
    pass  # TODO: exercise 1, replace with the fields in the docstring


def yeu_cau_phieu(van_ban: str) -> dict[str, Any]:
    raise NotImplementedError("TODO: exercise 1")


def doc_phieu(msg: Message) -> PhieuNuoc:
    raise NotImplementedError("TODO: exercise 1")
