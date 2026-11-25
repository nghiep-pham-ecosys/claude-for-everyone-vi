"""Module 03: one tool use round, written by hand step by step (mot_tool = one tool).

Claude does not run your code itself. It returns a tool_use block (tool name + input);
YOUR code runs the function, then sends the result back in a tool_result block.

Run:  CLAUDE_MOCK=1 uv run python en/modules/03-tool-use/python/01_mot_tool.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools_mau import GET_AQI, get_aqi  # noqa: E402

from claude_vi import ClaudeVi, text_of  # noqa: E402

client = ClaudeVi()
messages = [{"role": "user", "content": "How is the air in Hanoi today?"}]

# 1) Claude decides to call the tool
msg = client.create(messages=messages, tools=[GET_AQI])
print("stop_reason:", msg.stop_reason, "| blocks:", [b.type for b in msg.content])
call = next(b for b in msg.content if b.type == "tool_use")
print(f"Claude wants to call {call.name}({json.dumps(call.input, ensure_ascii=False)})")

# 2) Your code runs the real function
result = get_aqi(**call.input)

# 3) Send back: the assistant turn UNCHANGED (thinking included), then a user turn with the tool_result
messages += [
    {"role": "assistant", "content": msg.content},
    {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": call.id, "content": json.dumps(result, ensure_ascii=False)},
    ]},
]
final = client.create(messages=messages, tools=[GET_AQI])
print("\nstop_reason:", final.stop_reason)
print("Answer:", text_of(final))
