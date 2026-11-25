"""Module 07: append-only history and the prefix check.

A thinking block is valid only when everything sent BEFORE it stays the same: system, tools and earlier messages.
Changing system midway (adding the date, switching a mode...) breaks the thinking blocks of later turns.
On Haiku/Sonnet/Opus 5.5 and Fable 5.1/5.2, accounts created on or after 2026-08-31 get a 400 error.

The right way: keep system fixed, and add a new instruction as a message with role "system" after the user turn.

Run:  CLAUDE_MOCK=1 uv run python en/modules/07-thinking/python/05_append_only.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))

import anthropic  # noqa: E402
from claude_vi import ClaudeVi, text_of  # noqa: E402

client = ClaudeVi()
SYSTEM = "You are a chemistry teaching assistant. Answer briefly."
u1 = {"role": "user", "content": "What is pH?"}
a1 = client.create(system=SYSTEM, messages=[u1])
u2 = {"role": "user", "content": "Give an example."}
history = [u1, {"role": "assistant", "content": a1.content}, u2]

# WRONG: change system, then send the thinking block of turn 1 back
try:
    msg = client.create(system=SYSTEM + " Answer in Vietnamese.", messages=history)
    print("WRONG but no error: an account created before 2026-08-31 may not get a 400 on this model;"
          "\nthe mismatched block still reaches the model. People using your code with a new account get a 400.")
except anthropic.BadRequestError as e:
    error = (e.body or {}).get("error", {}).get("message", e.message) if isinstance(e.body, dict) else e.message
    print("WRONG -> 400:", error)

# RIGHT: system stays the same; the new instruction is a system message right after the user turn
msg = client.create(system=SYSTEM,
                    messages=[*history, {"role": "system", "content": "From now on, answer in Vietnamese."}])
print("\nRIGHT ->", text_of(msg))
print("\nA system message mid-conversation is not for outside data (tool results, the web): Claude treats it as"
      "\nan instruction from the developer. Outside data still goes in a tool_result.")
