"""Module 02 — effort: núm vặn giữa chất lượng, tốc độ và chi phí.

Không còn temperature. Trên model 5.x, output_config.effort (low, medium, high, xhigh, max)
điều khiển Claude bỏ bao nhiêu công: suy nghĩ, độ dài, số lần gọi tool.
Haiku 5.5 và Opus 5.5 mặc định "medium"; Sonnet 5.5 và Fable 5.1 mặc định "high".

Chạy:  CLAUDE_MOCK=1 uv run python modules/02-prompt-engineering/python/05_effort.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from claude_vi import ClaudeVi, estimate_cost_usd  # noqa: E402

client = ClaudeVi()
cau_hoi = "Một bể 2 m³ nước có pH 5,5. Cần thêm bao nhiêu NaOH 0,1 M để đạt pH 7? Nêu giả định."

print(f"{'effort':<8}{'thinking':>10}{'output':>8}{'USD':>12}")
for effort in ("low", "medium", "high"):
    msg = client.ask(cau_hoi, output_config={"effort": effort})
    u = msg.usage
    thinking = u.output_tokens_details.thinking_tokens if u.output_tokens_details else 0
    print(f"{effort:<8}{thinking:>10}{u.output_tokens:>8}{estimate_cost_usd(msg):>12.6f}")

print("\nSố token ở mock chỉ minh hoạ xu hướng. Đo trên chính bài toán của bạn trước khi chọn mức.")
