"""Module 01 — stop_reason, usage và chi phí.

stop_reason cho biết VÌ SAO response dừng. Đọc nó trước khi dùng text:
"max_tokens" nghĩa là câu trả lời bị cắt ngang.

Chạy:  CLAUDE_MOCK=1 uv run python modules/01-messages-api/python/03_stop_reason_usage.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from claude_vi import ClaudeVi, estimate_cost_usd, text_of  # noqa: E402

client = ClaudeVi()
prompt = "Kể tên 5 ứng dụng của Messages API, mỗi ý một dòng."

for max_tokens in (1024, 10):
    msg = client.ask(prompt, max_tokens=max_tokens)
    u = msg.usage
    thinking = u.output_tokens_details.thinking_tokens if u.output_tokens_details else 0
    print(f"--- max_tokens={max_tokens}")
    print("stop_reason:", msg.stop_reason)
    print("Trả lời:", repr(text_of(msg)))
    # Thinking tính là output token và tính vào max_tokens, kể cả khi text thinking bị ẩn
    print(f"Token: {u.input_tokens} vào / {u.output_tokens} ra (trong đó {thinking} token thinking)")
    print(f"Chi phí ước tính: ${estimate_cost_usd(msg):.6f}")
    if msg.stop_reason == "max_tokens":
        print("=> Bị cắt ngang. Tăng max_tokens hoặc yêu cầu trả lời ngắn hơn; đừng dùng text này như bản đầy đủ.")
    print()
