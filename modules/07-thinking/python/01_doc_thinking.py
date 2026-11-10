"""Module 07 — đọc block thinking: "omitted" và "summarized".

Trên model 5.x thinking bật sẵn, nhưng text của nó bị ẩn (display "omitted"). Muốn xem thì
đặt display "summarized": bạn nhận một BẢN TÓM TẮT do model khác viết, không phải suy nghĩ gốc.
Hai cách tính tiền như nhau: bạn trả cho toàn bộ token thinking, không phải số chữ bạn thấy.

Chạy:  CLAUDE_MOCK=1 uv run python modules/07-thinking/python/01_doc_thinking.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from claude_vi import ClaudeVi, estimate_cost_usd, text_of  # noqa: E402

client = ClaudeVi()
cau_hoi = "Một mẫu nước có pH 6,4. Nồng độ H+ gấp bao nhiêu lần mẫu có pH 7,1? Trả lời 2 câu."

for display in ("omitted", "summarized"):
    msg = client.ask(cau_hoi, thinking={"type": "adaptive", "display": display})
    u = msg.usage
    thinking_tokens = (u.output_tokens_details.thinking_tokens if u.output_tokens_details else None) or 0
    print(f"== display={display}")
    for b in msg.content:
        if b.type == "thinking":
            print(f"  thinking ({len(b.thinking)} ký tự hiển thị, chữ ký {b.signature[:16]}...): {b.thinking!r}")
        elif b.type == "redacted_thinking":
            print("  redacted_thinking: bị che vì lý do an toàn, không đọc được, vẫn phải gửi lại nguyên vẹn")
    print(f"  text: {text_of(msg)!r}")
    print(f"  token thinking bị tính: {thinking_tokens} / output {u.output_tokens}, ${estimate_cost_usd(msg):.6f}\n")

print('Không thấy block thinking nào? Với "adaptive", câu hỏi dễ có thể được trả lời mà không suy nghĩ.')
