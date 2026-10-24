"""Module 01 — streaming.

Streaming trả chữ dần dần qua server-sent events thay vì đợi cả response.
Người dùng thấy chữ sớm hơn, và request dài không bị mạng cắt vì im lặng quá lâu.

Chạy:  CLAUDE_MOCK=1 uv run python modules/01-messages-api/python/04_streaming.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from claude_vi import ClaudeVi, text_of  # noqa: E402

client = ClaudeVi()

with client.stream(messages=[{"role": "user", "content": "Viết một câu chào cho khoá học Claude."}]) as s:
    print("Đang nhận: ", end="")
    for chunk in s.text_stream:  # chỉ text_delta; thinking_delta bị bỏ qua
        print(chunk, end="|", flush=True)  # dấu | để thấy ranh giới từng mảnh
    print()
    msg = s.get_final_message()  # SDK ghép mọi event lại thành Message hoàn chỉnh

print("Các block:", [b.type for b in msg.content])
print("Ghép lại:", text_of(msg))
print("stop_reason:", msg.stop_reason, "| output_tokens:", msg.usage.output_tokens)
