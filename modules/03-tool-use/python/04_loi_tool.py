"""Module 03 — khi tool lỗi: trả is_error kèm lời nhắn có ích.

Đừng để exception làm sập vòng lặp, cũng đừng giấu lỗi. Gửi tool_result có is_error=True
và mô tả rõ chuyện gì xảy ra + nên làm gì tiếp, để Claude tự xoay xở hoặc báo người dùng.

Chạy:  CLAUDE_MOCK=1 uv run python modules/03-tool-use/python/04_loi_tool.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools_mau import TRA_AQI  # noqa: E402

from claude_vi import ClaudeVi, text_of  # noqa: E402


def tra_aqi_dang_bao_tri(thanh_pho: str) -> dict:
    raise ConnectionError("dịch vụ AQI đang bảo trì (HTTP 503)")


client = ClaudeVi()
messages = [{"role": "user", "content": "AQI ở Hà Nội bao nhiêu?"}]
msg = client.create(messages=messages, tools=[TRA_AQI])
call = next(b for b in msg.content if b.type == "tool_use")

try:
    content, is_error = str(tra_aqi_dang_bao_tri(**call.input)), False
except Exception as e:  # noqa: BLE001 - mọi lỗi của tool đều phải về tay Claude
    content = f"{type(e).__name__}: {e}. Thử lại sau khoảng 10 phút; đừng đoán số liệu."
    is_error = True

messages += [
    {"role": "assistant", "content": msg.content},
    {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": call.id, "content": content, "is_error": is_error},
    ]},
]
final = client.create(messages=messages, tools=[TRA_AQI])
print("tool_result gửi đi:", content)
print("Trả lời:", text_of(final))
