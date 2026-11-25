"""Module 02: effort, the knob between quality, speed and cost.

There is no temperature any more. On 5.x models, output_config.effort (low, medium, high, xhigh, max)
controls how much work Claude puts in: thinking, length, number of tool calls.
Haiku 5.5 and Opus 5.5 default to "medium"; Sonnet 5.5 and Fable 5.1 default to "high".

Run:  CLAUDE_MOCK=1 uv run python en/modules/02-prompt-engineering/python/05_effort.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))

from claude_vi import ClaudeVi, estimate_cost_usd  # noqa: E402

client = ClaudeVi()
question = "A tank holds 2 m³ of water at pH 5.5. How much 0.1 M NaOH is needed to reach pH 7? State your assumptions."

print(f"{'effort':<8}{'thinking':>10}{'output':>8}{'USD':>12}")
for effort in ("low", "medium", "high"):
    msg = client.ask(question, output_config={"effort": effort})
    u = msg.usage
    thinking = u.output_tokens_details.thinking_tokens if u.output_tokens_details else 0
    print(f"{effort:<8}{thinking:>10}{u.output_tokens:>8}{estimate_cost_usd(msg):>12.6f}")

print("\nThe mock token counts only show the trend. Measure on your own task before you choose a level.")
