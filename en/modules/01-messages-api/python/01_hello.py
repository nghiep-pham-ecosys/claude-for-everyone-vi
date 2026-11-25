"""Module 01: the first call.

Run:  CLAUDE_MOCK=1 uv run python en/modules/01-messages-api/python/01_hello.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))

from claude_vi import ClaudeVi, estimate_cost_usd, text_of  # noqa: E402

client = ClaudeVi()
msg = client.ask(
    "Explain prompt caching to a first-year student, in 3 sentences at most.",
    system="You are a teaching assistant. Answer in English.",
)

print("Blocks in the response:", [b.type for b in msg.content])
print("Answer:", text_of(msg))
print("stop_reason:", msg.stop_reason)
print(f"Tokens: {msg.usage.input_tokens} in / {msg.usage.output_tokens} out")
print(f"Estimated cost: ${estimate_cost_usd(msg):.6f}")
