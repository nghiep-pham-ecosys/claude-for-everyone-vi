"""Module 03: tool_choice: let Claude decide, or forbid tools.

The repo uses only "auto" (the default) and "none". "any"/"tool" (force a tool call) return 400 on
Opus 5.5, Sonnet 5.5, Fable 5.1. To make the tool input always match the schema, use strict tool use.

Run:  CLAUDE_MOCK=1 uv run python en/modules/03-tool-use/python/03_tool_choice.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools_mau import GET_AQI, GET_TEMPERATURE  # noqa: E402

from claude_vi import ClaudeVi  # noqa: E402

client = ClaudeVi()
tools = [GET_AQI, GET_TEMPERATURE]
messages = [{"role": "user", "content": "Compare the air and the temperature in Hanoi and Da Nang."}]

choices = {
    "auto (the default)": {"type": "auto"},
    "auto, at most 1 tool per turn": {"type": "auto", "disable_parallel_tool_use": True},
    "none (no tools)": {"type": "none"},
}
for name, choice in choices.items():
    msg = client.create(messages=messages, tools=tools, tool_choice=choice)
    called = [b.name for b in msg.content if b.type == "tool_use"]
    print(f"{name:<32} stop_reason={msg.stop_reason:<9} tools called: {called}")

print("\nWant Claude to use tools more? Say it in system: 'Use the tools to check before you answer.'")
