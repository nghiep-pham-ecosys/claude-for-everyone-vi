"""Module 07: streaming thinking.

A thinking block streams as thinking_delta events, then one signature_delta right before content_block_stop.
With display "omitted", thinking_delta carries an empty string: the server skips the thinking, so the text
of the answer arrives sooner. Hiding thinking makes it faster, not cheaper.

Run:  CLAUDE_MOCK=1 uv run python en/modules/07-thinking/python/04_stream_thinking.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))

from claude_vi import ClaudeVi  # noqa: E402

client = ClaudeVi()
with client.stream(messages=[{"role": "user", "content": "Why is the sky blue? Two sentences."}],
                   thinking={"type": "adaptive", "display": "summarized"}) as s:
    current = None
    for event in s:
        if event.type == "content_block_start":
            current = event.content_block.type
            print(f"\n[{current}] ", end="")
        elif event.type == "content_block_delta":
            d = event.delta
            if d.type == "thinking_delta":
                print(d.thinking, end="", flush=True)
            elif d.type == "text_delta":
                print(d.text, end="", flush=True)
            elif d.type == "signature_delta":
                print(f" <signature, {len(d.signature)} characters>", end="")
    msg = s.get_final_message()   # puts the thinking block and its signature together; do not join deltas

print(f"\n\nFull message: {[b.type for b in msg.content]}; send msg.content back unchanged on the next turn.")
