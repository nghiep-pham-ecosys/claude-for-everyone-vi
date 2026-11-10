"""Bài 1 — phiếu quan trắc nước bằng Pydantic + structured outputs. (LỜI GIẢI)"""
from __future__ import annotations

import json
from typing import Any, Literal

from anthropic import transform_schema
from anthropic.types import Message
from claude_vi import text_of
from pydantic import BaseModel, Field


class PhieuNuoc(BaseModel):
    ma_mau: str = Field(description="mã mẫu, ví dụ W1")
    ph: float = Field(ge=0, le=14)
    do_mg_l: float = Field(ge=0, description="oxy hoà tan, mg/L")
    danh_gia: Literal["dat", "khong_dat"]
    ghi_chu: str | None = None


def yeu_cau_phieu(van_ban: str) -> dict[str, Any]:
    return {
        "system": ("Bạn chuyển phiếu quan trắc nước thành dữ liệu. Chỉ dùng số liệu có trong văn bản, "
                   "vì kết quả được kiểm tự động."),
        "messages": [{"role": "user", "content": f"<van_ban>{van_ban}</van_ban>"}],
        "output_config": {"format": {"type": "json_schema", "schema": transform_schema(PhieuNuoc)}},
    }


def doc_phieu(msg: Message) -> PhieuNuoc:
    if msg.stop_reason != "end_turn":
        raise ValueError(f"Không dùng được kết quả: stop_reason={msg.stop_reason}")
    data = json.loads(text_of(msg))
    if isinstance(data.get("danh_gia"), str):
        data["danh_gia"] = data["danh_gia"].lower()      # enum có thể bị đổi hoa thường
    return PhieuNuoc.model_validate(data)                # ValidationError là một ValueError
