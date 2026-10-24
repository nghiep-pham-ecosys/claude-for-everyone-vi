"""Module 03 — vì sao phải gửi lại block thinking NGUYÊN VẸN trong vòng lặp tool.

Trên model 5.x, lượt assistant chứa tool_use thường có block thinking đứng trước.
Nếu bạn lọc bỏ hay sửa block đó khi gửi lại, API trả 400. Mock của repo mô phỏng đúng lỗi này.

Chạy:  CLAUDE_MOCK=1 uv run python modules/03-tool-use/python/05_giu_thinking.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import anthropic  # noqa: E402
from tools_mau import TRA_AQI, tra_aqi  # noqa: E402

from claude_vi import ClaudeVi, text_of  # noqa: E402

client = ClaudeVi()
cau_hoi = {"role": "user", "content": "AQI Hà Nội?"}
msg = client.create(messages=[cau_hoi], tools=[TRA_AQI])
call = next(b for b in msg.content if b.type == "tool_use")
ket_qua = {"type": "tool_result", "tool_use_id": call.id, "content": str(tra_aqi(**call.input))}

print("Block trong lượt assistant:", [b.type for b in msg.content])

# SAI: chỉ giữ text + tool_use cho "gọn"
gon = [b for b in msg.content if b.type != "thinking"]
try:
    client.create(messages=[cau_hoi, {"role": "assistant", "content": gon},
                            {"role": "user", "content": [ket_qua]}], tools=[TRA_AQI])
except anthropic.BadRequestError as e:
    print("\nSAI -> 400:", e.message[:140], "...")

# ĐÚNG: gửi lại msg.content y nguyên
final = client.create(messages=[cau_hoi, {"role": "assistant", "content": msg.content},
                                {"role": "user", "content": [ket_qua]}], tools=[TRA_AQI])
print("\nĐÚNG ->", text_of(final))
