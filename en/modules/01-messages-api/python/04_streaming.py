"""Module 01: streaming.

Streaming returns the text bit by bit through server-sent events instead of waiting for the whole response.
The user sees text sooner, and a long request is not cut by the network for staying silent too long.

Run:  CLAUDE_MOCK=1 uv run python en/modules/01-messages-api/python/04_streaming.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))

from claude_vi import ClaudeVi, text_of  # noqa: E402

client = ClaudeVi()

with client.stream(messages=[{"role": "user", "content": "Write a welcome line for a Claude course."}]) as s:
    print("Receiving: ", end="")
    for chunk in s.text_stream:  # text_delta only; thinking_delta is skipped
        print(chunk, end="|", flush=True)  # the | marks the border of each piece
    print()
    msg = s.get_final_message()  # the SDK joins every event into a full Message

print("Blocks:", [b.type for b in msg.content])
print("Joined:", text_of(msg))
print("stop_reason:", msg.stop_reason, "| output_tokens:", msg.usage.output_tokens)
