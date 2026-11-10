"""Module 07 — thinking ăn vào max_tokens.

max_tokens là trần CỨNG cho mọi token output của lượt này: thinking + text.
Effort chỉ là tín hiệu mềm. Đặt max_tokens quá sát thì thinking dùng hết chỗ, text bị cắt hoặc rỗng,
và bạn vẫn trả tiền cho phần thinking đó.

Chạy:  CLAUDE_MOCK=1 uv run python modules/07-thinking/python/03_max_tokens.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from claude_vi import ClaudeVi, text_of  # noqa: E402

client = ClaudeVi()
cau_hoi = "Giải thích ngắn vì sao DO (oxy hoà tan) giảm khi nước ấm lên."

print(f"{'effort':<8}{'max_tokens':>11}{'thinking':>10}{'output':>8}  {'stop_reason':<12} text")
for effort, max_tokens in [("high", 1024), ("high", 16), ("high", 12), ("low", 16)]:
    msg = client.ask(cau_hoi, max_tokens=max_tokens, output_config={"effort": effort})
    u = msg.usage
    thinking = (u.output_tokens_details.thinking_tokens if u.output_tokens_details else None) or 0
    text = text_of(msg)
    print(f"{effort:<8}{max_tokens:>11}{thinking:>10}{u.output_tokens:>8}  {msg.stop_reason:<12} {text[:40]!r}")

print("\nstop_reason=max_tokens và text rỗng: thinking đã dùng hết trần. Tăng max_tokens trước, rồi mới giảm effort."
      "\nTrên API thật, max_tokens > 21.333 thì SDK bắt dùng stream (client.stream) để tránh timeout.")
