"""Module 01 — lời gọi đầu tiên.

Chạy:  CLAUDE_MOCK=1 uv run python modules/01-messages-api/python/hello.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from claude_vi import ClaudeVi, estimate_cost_usd, text_of  # noqa: E402

client = ClaudeVi()
msg = client.ask(
    "Giải thích prompt caching cho sinh viên năm nhất, tối đa 3 câu.",
    system="Bạn là trợ giảng, trả lời bằng tiếng Việt.",
)

print("Các block trong response:", [b.type for b in msg.content])
print("Trả lời:", text_of(msg))
print("stop_reason:", msg.stop_reason)
print(f"Token: {msg.usage.input_tokens} vào / {msg.usage.output_tokens} ra")
print(f"Chi phí ước tính: ${estimate_cost_usd(msg):.6f}")
