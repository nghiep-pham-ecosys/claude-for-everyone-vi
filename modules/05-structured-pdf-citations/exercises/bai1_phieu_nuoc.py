"""Bài 1 — phiếu quan trắc nước bằng Pydantic + structured outputs.

class PhieuNuoc(BaseModel) — viết các trường:
    - ma_mau: str
    - ph: float, nằm trong 0–14            (Field(ge=..., le=...))
    - do_mg_l: float, không âm              (oxy hoà tan, mg/L)
    - danh_gia: chỉ "dat" hoặc "khong_dat"  (Literal)
    - ghi_chu: str hoặc None, mặc định None (trường optional duy nhất)

yeu_cau_phieu(van_ban) -> dict tham số cho client.create(**...)
    - "system": nói rõ nhiệm vụ và vì sao chỉ được dùng số liệu có trong văn bản.
    - "messages": một lượt user, bọc văn bản trong <van_ban>...</van_ban>.
    - "output_config": {"format": {"type": "json_schema", "schema": transform_schema(PhieuNuoc)}}
      Gửi thẳng PhieuNuoc.model_json_schema() sẽ lỗi 400 (có "minimum", thiếu additionalProperties).

doc_phieu(msg) -> PhieuNuoc
    - stop_reason khác "end_turn" -> raise ValueError.
    - Claude có thể đổi hoa thường của enum ("Dat"): chuẩn hoá danh_gia về chữ thường trước khi kiểm.
    - Kiểm bằng PhieuNuoc.model_validate(...): pH 15 vẫn "đúng schema" nhưng sai ràng buộc của bạn,
      và phải bị bắt ở đây (pydantic.ValidationError là một ValueError).

Chấm:  CHAM=exercises uv run pytest modules/05-structured-pdf-citations -q
"""
from __future__ import annotations

import json  # noqa: F401
from typing import Any, Literal  # noqa: F401

from anthropic import transform_schema  # noqa: F401
from anthropic.types import Message
from claude_vi import text_of  # noqa: F401
from pydantic import BaseModel, Field  # noqa: F401


class PhieuNuoc(BaseModel):
    pass  # TODO: bài 1 — thay bằng các trường ở docstring


def yeu_cau_phieu(van_ban: str) -> dict[str, Any]:
    raise NotImplementedError("TODO: bài 1")


def doc_phieu(msg: Message) -> PhieuNuoc:
    raise NotImplementedError("TODO: bài 1")
