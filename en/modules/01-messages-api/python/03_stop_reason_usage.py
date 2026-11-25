"""Module 01: stop_reason, usage and cost.

stop_reason tells you WHY the response stopped. Read it before you use the text:
"max_tokens" means the answer was cut off.

Run:  CLAUDE_MOCK=1 uv run python en/modules/01-messages-api/python/03_stop_reason_usage.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))

from claude_vi import ClaudeVi, estimate_cost_usd, text_of  # noqa: E402

client = ClaudeVi()
prompt = "Name 5 uses of the Messages API, one per line."

for max_tokens in (1024, 10):
    msg = client.ask(prompt, max_tokens=max_tokens)
    u = msg.usage
    thinking = u.output_tokens_details.thinking_tokens if u.output_tokens_details else 0
    print(f"--- max_tokens={max_tokens}")
    print("stop_reason:", msg.stop_reason)
    print("Answer:", repr(text_of(msg)))
    # Thinking counts as output tokens and toward max_tokens, even when the thinking text is hidden
    print(f"Tokens: {u.input_tokens} in / {u.output_tokens} out ({thinking} of them thinking tokens)")
    print(f"Estimated cost: ${estimate_cost_usd(msg):.6f}")
    if msg.stop_reason == "max_tokens":
        print("=> Cut off. Raise max_tokens or ask for a shorter answer; do not use this text as complete.")
    print()
