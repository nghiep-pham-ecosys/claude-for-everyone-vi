"""Module 05 — schema viết bằng Pydantic, ràng buộc kiểm trong code.

Structured outputs không nhận minimum/maximum. anthropic.transform_schema() bỏ các ràng buộc đó
khỏi schema gửi đi và chép chúng vào description. Bạn vẫn giữ ràng buộc ở phía mình:
Pydantic kiểm lại khi đọc kết quả.

Chạy:  CLAUDE_MOCK=1 uv run python modules/05-structured-pdf-citations/python/01_pydantic_schema.py
"""
import json
import sys
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from anthropic import transform_schema  # noqa: E402
from claude_vi import ClaudeVi, text_of  # noqa: E402
from pydantic import BaseModel, Field, ValidationError  # noqa: E402


class PhepDo(BaseModel):
    mau: str = Field(description="mã mẫu, ví dụ W1")
    dai_luong: Literal["pH", "DO", "do_duc"]
    gia_tri: float = Field(ge=0)
    don_vi: str = Field(description="đơn vị như trong văn bản; chuỗi rỗng nếu không có")
    ghi_chu: str | None = None          # optional + union: tính vào giới hạn 24 optional / 16 union


class Bang(BaseModel):
    phep_do: list[PhepDo]


schema = transform_schema(Bang)
print("Schema gửi đi (ge=0 đã chuyển vào description):")
print(json.dumps(schema["$defs"]["PhepDo"]["properties"]["gia_tri"], ensure_ascii=False))

msg = ClaudeVi().ask(
    "<van_ban>Mẫu W1: pH 7,1; DO 6,2 mg/L. Mẫu W2: độ đục 12 NTU.</van_ban>\n"
    "Tách mỗi phép đo thành một dòng.",
    output_config={"format": {"type": "json_schema", "schema": schema}},
)
if msg.stop_reason != "end_turn":
    raise SystemExit(f"Không dùng được kết quả: stop_reason={msg.stop_reason}")

try:
    bang = Bang.model_validate_json(text_of(msg))   # kiểm cả ge=0 mà API không đảm bảo
except ValidationError as e:
    raise SystemExit(f"JSON đúng schema nhưng sai ràng buộc của bạn:\n{e}") from None
for d in bang.phep_do:
    print(d)
