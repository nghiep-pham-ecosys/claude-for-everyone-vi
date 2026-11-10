"""Module 07 — stream thinking.

Block thinking stream bằng thinking_delta, rồi một signature_delta ngay trước content_block_stop.
Với display "omitted", thinking_delta mang chuỗi rỗng: server bỏ qua phần thinking nên chữ của câu trả lời
tới sớm hơn. Ẩn thinking giúp nhanh hơn, không rẻ hơn.

Chạy:  CLAUDE_MOCK=1 uv run python modules/07-thinking/python/04_stream_thinking.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from claude_vi import ClaudeVi  # noqa: E402

client = ClaudeVi()
with client.stream(messages=[{"role": "user", "content": "Vì sao bầu trời màu xanh? Hai câu."}],
                   thinking={"type": "adaptive", "display": "summarized"}) as s:
    dang_o = None
    for event in s:
        if event.type == "content_block_start":
            dang_o = event.content_block.type
            print(f"\n[{dang_o}] ", end="")
        elif event.type == "content_block_delta":
            d = event.delta
            if d.type == "thinking_delta":
                print(d.thinking, end="", flush=True)
            elif d.type == "text_delta":
                print(d.text, end="", flush=True)
            elif d.type == "signature_delta":
                print(f" <chữ ký {len(d.signature)} ký tự>", end="")
    msg = s.get_final_message()   # ghép block thinking + chữ ký giúp bạn, đừng tự nối delta

print(f"\n\nMessage hoàn chỉnh: {[b.type for b in msg.content]}, gửi lại nguyên msg.content ở lượt sau.")
