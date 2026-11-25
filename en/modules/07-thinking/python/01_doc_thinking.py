"""Module 07: read the thinking block, "omitted" and "summarized" (doc_thinking = read thinking).

On 5.x models thinking is on by default, but its text is hidden (display "omitted"). To see it,
set display "summarized": you get a SUMMARY written by another model, not the original thinking.
Both are billed the same: you pay for all the thinking tokens, not for the text you see.

Run:  CLAUDE_MOCK=1 uv run python en/modules/07-thinking/python/01_doc_thinking.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))

from claude_vi import ClaudeVi, estimate_cost_usd, text_of  # noqa: E402

client = ClaudeVi()
question = ("A water sample has pH 6.4. How many times higher is its H+ concentration than a sample "
            "with pH 7.1? Answer in 2 sentences.")

for display in ("omitted", "summarized"):
    msg = client.ask(question, thinking={"type": "adaptive", "display": display})
    u = msg.usage
    thinking_tokens = (u.output_tokens_details.thinking_tokens if u.output_tokens_details else None) or 0
    print(f"== display={display}")
    for b in msg.content:
        if b.type == "thinking":
            print(f"  thinking ({len(b.thinking)} visible characters, signature {b.signature[:16]}...): "
                  f"{b.thinking!r}")
        elif b.type == "redacted_thinking":
            print("  redacted_thinking: hidden for safety reasons, unreadable, still must be sent back unchanged")
    print(f"  text: {text_of(msg)!r}")
    print(f"  thinking tokens billed: {thinking_tokens} / output {u.output_tokens}, "
          f"${estimate_cost_usd(msg):.6f}\n")

print('No thinking block at all? With "adaptive", an easy question may be answered without thinking.')
