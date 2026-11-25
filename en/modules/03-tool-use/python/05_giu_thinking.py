"""Module 03: why you must send the thinking block back UNCHANGED in a tool loop (giu_thinking = keep thinking).

On 5.x models, an assistant turn with tool_use usually has a thinking block in front.
If you drop or edit that block when you send it back, the API returns 400. The repo's mock simulates this error.

Run:  CLAUDE_MOCK=1 uv run python en/modules/03-tool-use/python/05_giu_thinking.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import anthropic  # noqa: E402
from tools_mau import GET_AQI, get_aqi  # noqa: E402

from claude_vi import ClaudeVi, text_of  # noqa: E402

client = ClaudeVi()
question = {"role": "user", "content": "AQI in Hanoi?"}
msg = client.create(messages=[question], tools=[GET_AQI])
call = next(b for b in msg.content if b.type == "tool_use")
result = {"type": "tool_result", "tool_use_id": call.id, "content": str(get_aqi(**call.input))}

print("Blocks in the assistant turn:", [b.type for b in msg.content])

# WRONG: keep only text + tool_use "to keep it short"
trimmed = [b for b in msg.content if b.type != "thinking"]
try:
    client.create(messages=[question, {"role": "assistant", "content": trimmed},
                            {"role": "user", "content": [result]}], tools=[GET_AQI])
except anthropic.BadRequestError as e:
    print("\nWRONG -> 400:", e.message[:140], "...")

# RIGHT: send msg.content back as it is
final = client.create(messages=[question, {"role": "assistant", "content": msg.content},
                                {"role": "user", "content": [result]}], tools=[GET_AQI])
print("\nRIGHT ->", text_of(final))
