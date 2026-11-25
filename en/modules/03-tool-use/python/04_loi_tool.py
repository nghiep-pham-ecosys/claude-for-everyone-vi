"""Module 03: when a tool fails, return is_error with a useful message (loi_tool = tool error).

Do not let an exception crash the loop, and do not hide the error either. Send a tool_result with is_error=True
and say clearly what happened and what to do next, so Claude can work around it or tell the user.

Run:  CLAUDE_MOCK=1 uv run python en/modules/03-tool-use/python/04_loi_tool.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools_mau import GET_AQI  # noqa: E402

from claude_vi import ClaudeVi, text_of  # noqa: E402


def get_aqi_under_maintenance(city: str) -> dict:
    raise ConnectionError("the AQI service is under maintenance (HTTP 503)")


client = ClaudeVi()
messages = [{"role": "user", "content": "What is the AQI in Hanoi?"}]
msg = client.create(messages=messages, tools=[GET_AQI])
call = next(b for b in msg.content if b.type == "tool_use")

try:
    content, is_error = str(get_aqi_under_maintenance(**call.input)), False
except Exception as e:  # noqa: BLE001 - every tool error must reach Claude
    content = f"{type(e).__name__}: {e}. Try again in about 10 minutes; do not guess the numbers."
    is_error = True

messages += [
    {"role": "assistant", "content": msg.content},
    {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": call.id, "content": content, "is_error": is_error},
    ]},
]
final = client.create(messages=messages, tools=[GET_AQI])
print("tool_result sent:", content)
print("Answer:", text_of(final))
