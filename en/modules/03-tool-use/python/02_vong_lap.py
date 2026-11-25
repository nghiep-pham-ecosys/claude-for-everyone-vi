"""Module 03: the tool loop (agentic loop) with several tools called in parallel (vong_lap = loop).

Loop: call Claude -> if stop_reason is "tool_use", run EVERY tool_use in the response,
send EVERY result in ONE user turn -> call again. Stop when stop_reason is not "tool_use".

Run:  CLAUDE_MOCK=1 uv run python en/modules/03-tool-use/python/02_vong_lap.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools_mau import GET_AQI, GET_TEMPERATURE, REGISTRY  # noqa: E402

from claude_vi import ClaudeVi, text_of  # noqa: E402

client = ClaudeVi()
tools = [GET_AQI, GET_TEMPERATURE]
messages = [{"role": "user", "content": "Is Hanoi hot right now? Should I go for a run outside?"}]

for turn in range(1, 6):  # always cap the number of turns: an agent must not loop forever
    msg = client.create(messages=messages, tools=tools)
    print(f"Turn {turn}: stop_reason={msg.stop_reason}")
    if msg.stop_reason != "tool_use":
        break
    messages.append({"role": "assistant", "content": msg.content})
    results = []
    for block in msg.content:
        if block.type != "tool_use":
            continue
        output = REGISTRY[block.name](**block.input)
        print(f"  run {block.name}{block.input} -> {output}")
        results.append({"type": "tool_result", "tool_use_id": block.id,
                        "content": json.dumps(output, ensure_ascii=False)})
    messages.append({"role": "user", "content": results})  # every result in ONE user turn
else:
    raise SystemExit("Over 5 turns and still not done: stopping to avoid wasting money.")

print("\nAnswer:", text_of(msg))
