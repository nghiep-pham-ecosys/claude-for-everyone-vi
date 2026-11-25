"""Module 07: thinking eats into max_tokens.

max_tokens is a HARD cap on every output token of this turn: thinking + text.
Effort is only a soft signal. Set max_tokens too tight and thinking uses up the room: the text is cut off
or empty, and you still pay for that thinking.

Run:  CLAUDE_MOCK=1 uv run python en/modules/07-thinking/python/03_max_tokens.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))

from claude_vi import ClaudeVi, text_of  # noqa: E402

client = ClaudeVi()
question = "Briefly explain why DO (dissolved oxygen) goes down when water gets warmer."

print(f"{'effort':<8}{'max_tokens':>11}{'thinking':>10}{'output':>8}  {'stop_reason':<12} text")
for effort, max_tokens in [("high", 1024), ("high", 16), ("high", 12), ("low", 16)]:
    msg = client.ask(question, max_tokens=max_tokens, output_config={"effort": effort})
    u = msg.usage
    thinking = (u.output_tokens_details.thinking_tokens if u.output_tokens_details else None) or 0
    text = text_of(msg)
    print(f"{effort:<8}{max_tokens:>11}{thinking:>10}{u.output_tokens:>8}  {msg.stop_reason:<12} {text[:40]!r}")

print("\nstop_reason=max_tokens and empty text: thinking used up the cap. Raise max_tokens first, then lower effort."
      "\nWith the real API, max_tokens > 21,333 makes the SDK require streaming (client.stream) to avoid timeouts.")
