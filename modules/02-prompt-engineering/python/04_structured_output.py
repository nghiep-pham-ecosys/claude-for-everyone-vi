"""Module 02 — ép định dạng bằng structured outputs.

Trước đây người ta prefill "{" để ép JSON. Trên model 5.x prefill trả 400.
Cách đúng: output_config.format với JSON schema. API đảm bảo text trả về khớp schema
(trừ khi stop_reason là "refusal" hoặc "max_tokens" — luôn kiểm tra).

Chạy:  CLAUDE_MOCK=1 uv run python modules/02-prompt-engineering/python/04_structured_output.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from claude_vi import ClaudeVi, text_of  # noqa: E402

NHOM = ["giang_day", "danh_gia", "co_so_vat_chat", "khac"]
schema = {
    "type": "object",
    "properties": {
        "nhom": {"type": "string", "enum": NHOM},
        "muc_do": {"type": "integer", "description": "1 (nhẹ) đến 3 (nghiêm trọng)"},
        "ly_do": {"type": "string"},
    },
    "required": ["nhom", "muc_do", "ly_do"],
    "additionalProperties": False,  # bắt buộc với structured outputs
}

msg = ClaudeVi().ask(
    "Phân loại phản hồi: <phan_hoi>Máy chiếu phòng B2 mờ, ngồi cuối không đọc được slide.</phan_hoi>",
    output_config={"format": {"type": "json_schema", "schema": schema}},
)

if msg.stop_reason != "end_turn":
    raise SystemExit(f"Không dùng được kết quả: stop_reason={msg.stop_reason}")
data = json.loads(text_of(msg))
# Schema không cho đặt minimum/maximum, nên tự kiểm khoảng giá trị trong code
if not 1 <= data["muc_do"] <= 3:
    print(f"muc_do={data['muc_do']} ngoài khoảng 1–3 -> cần xử lý (ở mock luôn là 0)")
print(json.dumps(data, ensure_ascii=False, indent=2))
