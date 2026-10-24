"""Module 03 — một vòng tool use, viết tay từng bước.

Claude không tự chạy code của bạn. Nó trả về một block tool_use (tên tool + input);
code của BẠN chạy hàm, rồi gửi kết quả lại trong block tool_result.

Chạy:  CLAUDE_MOCK=1 uv run python modules/03-tool-use/python/01_mot_tool.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools_mau import TRA_AQI, tra_aqi  # noqa: E402

from claude_vi import ClaudeVi, text_of  # noqa: E402

client = ClaudeVi()
messages = [{"role": "user", "content": "Không khí ở Hà Nội hôm nay thế nào?"}]

# 1) Claude quyết định gọi tool
msg = client.create(messages=messages, tools=[TRA_AQI])
print("stop_reason:", msg.stop_reason, "| blocks:", [b.type for b in msg.content])
call = next(b for b in msg.content if b.type == "tool_use")
print(f"Claude muốn gọi {call.name}({json.dumps(call.input, ensure_ascii=False)})")

# 2) Code của bạn chạy hàm thật
ket_qua = tra_aqi(**call.input)

# 3) Gửi lại: lượt assistant NGUYÊN VẸN (kể cả thinking), rồi lượt user chứa tool_result
messages += [
    {"role": "assistant", "content": msg.content},
    {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": call.id, "content": json.dumps(ket_qua, ensure_ascii=False)},
    ]},
]
final = client.create(messages=messages, tools=[TRA_AQI])
print("\nstop_reason:", final.stop_reason)
print("Trả lời:", text_of(final))
