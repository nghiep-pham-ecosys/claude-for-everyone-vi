"""Module 03 — tool_choice: để Claude tự quyết, hoặc cấm dùng tool.

Repo chỉ dùng "auto" (mặc định) và "none". "any"/"tool" (ép gọi tool) trả 400 trên
Opus 5.5, Sonnet 5.5, Fable 5.1 — muốn đầu vào tool luôn đúng schema thì dùng strict tool use.

Chạy:  CLAUDE_MOCK=1 uv run python modules/03-tool-use/python/03_tool_choice.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools_mau import TRA_AQI, TRA_NHIET_DO  # noqa: E402

from claude_vi import ClaudeVi  # noqa: E402

client = ClaudeVi()
tools = [TRA_AQI, TRA_NHIET_DO]
messages = [{"role": "user", "content": "So sánh không khí và nhiệt độ ở Hà Nội với Đà Nẵng."}]

cac_lua_chon = {
    "auto (mặc định)": {"type": "auto"},
    "auto, tối đa 1 tool mỗi lượt": {"type": "auto", "disable_parallel_tool_use": True},
    "none (không dùng tool)": {"type": "none"},
}
for ten, choice in cac_lua_chon.items():
    msg = client.create(messages=messages, tools=tools, tool_choice=choice)
    goi = [b.name for b in msg.content if b.type == "tool_use"]
    print(f"{ten:<32} stop_reason={msg.stop_reason:<9} tool gọi: {goi}")

print("\nMuốn Claude dùng tool nhiều hơn? Nói trong system: 'Dùng tool để kiểm tra trước khi trả lời.'")
