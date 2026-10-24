"""Module 01 — hội thoại nhiều lượt.

API không nhớ gì giữa hai lần gọi (stateless). Muốn Claude "nhớ" lượt trước,
mỗi request phải gửi lại toàn bộ lịch sử.

Chạy:  CLAUDE_MOCK=1 uv run python modules/01-messages-api/python/02_multi_turn.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from claude_vi import ClaudeVi, text_of  # noqa: E402

client = ClaudeVi()
system = "Bạn là trợ giảng, trả lời bằng tiếng Việt, tối đa 2 câu."
history: list[dict] = []

for question in ["Prompt caching là gì?", "Vậy khi nào KHÔNG nên dùng nó?"]:
    history.append({"role": "user", "content": question})
    msg = client.create(system=system, messages=history)
    # Gửi lại NGUYÊN VẸN msg.content (kể cả block thinking), không chỉ phần text.
    # Lịch sử chỉ được nối thêm (append-only): sửa lượt cũ có thể làm block thinking bị từ chối.
    history.append({"role": "assistant", "content": msg.content})
    print(f"Hỏi: {question}\nĐáp: {text_of(msg)}\n")

print("Vai trò trong lịch sử:", [m["role"] for m in history])
print(f"Lượt cuối gửi {len(history) - 1} message -> input_tokens tăng theo từng lượt")
