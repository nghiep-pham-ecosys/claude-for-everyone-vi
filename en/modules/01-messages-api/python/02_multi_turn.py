"""Module 01: a multi-turn conversation.

The API remembers nothing between two calls (it is stateless). For Claude to "remember"
an earlier turn, each request must send the whole history again.

Run:  CLAUDE_MOCK=1 uv run python en/modules/01-messages-api/python/02_multi_turn.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))

from claude_vi import ClaudeVi, text_of  # noqa: E402

client = ClaudeVi()
system = "You are a teaching assistant. Answer in English, in 2 sentences at most."
history: list[dict] = []

for question in ["What is prompt caching?", "So when should I NOT use it?"]:
    history.append({"role": "user", "content": question})
    msg = client.create(system=system, messages=history)
    # Send msg.content back UNCHANGED (thinking blocks included), not just the text.
    # The history is append-only: editing an old turn can make a thinking block get rejected.
    history.append({"role": "assistant", "content": msg.content})
    print(f"Q: {question}\nA: {text_of(msg)}\n")

print("Roles in the history:", [m["role"] for m in history])
print(f"The last turn sent {len(history) - 1} messages -> input_tokens grows with every turn")
