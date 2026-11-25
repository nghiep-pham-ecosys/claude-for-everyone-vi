"""Module 08: prompt chaining with a gate (chuoi_co_cong = chain with a gate).

Step 1 extracts one measurement with structured outputs. The gate is CODE: the right quantity, the right unit,
a value in the valid range. If the gate fails, the chain stops and says why; step 2 is never called.

In mock mode a number in the JSON is always 0 and a string is "[MOCK]", so the gate fails: that is exactly what
this script wants to show. The last part passes a valid step 1 result (written by hand) through the gate,
to show the path that goes on.

Run:  CLAUDE_MOCK=1 uv run python en/modules/08-agents-workflows/python/02_chuoi_co_cong.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from phong_thi_nghiem import make_client, read_page  # noqa: E402

from claude_vi import text_of  # noqa: E402

# Valid range and unit from handbook page 01 (fictional): electrode slope 95–105 %
RANGES = {"electrode_slope": (95.0, 105.0, "%")}
SCHEMA = {
    "type": "object",
    "properties": {
        "quantity": {"type": "string", "enum": list(RANGES)},
        "value": {"type": "number"},
        "unit": {"type": "string"},
    },
    "required": ["quantity", "value", "unit"],
    "additionalProperties": False,
}


def gate(data: dict) -> str | None:
    """None if it passes, otherwise the reason it failed. No call to Claude: the gate is code, cheap and certain."""
    lo, hi, unit = RANGES[data["quantity"]]
    if data["unit"] != unit:
        return f"unit '{data['unit']}' is not '{unit}'"
    if not lo <= data["value"] <= hi:
        return f"value {data['value']} is outside {lo}–{hi} {unit}"
    return None


def step_2(client, data: dict) -> str:
    msg = client.ask(f"Write a one-sentence comment on this measurement: {json.dumps(data, ensure_ascii=False)}",
                     system="Answer in one sentence, in English.")
    return text_of(msg)


client = make_client()
text = read_page("01_hieu_chuan_ph") + "\n\nToday's result: the measured electrode slope is 98.6 %."
msg = client.ask(f"<text>\n{text}\n</text>\n\nExtract today's measurement.",
                 output_config={"format": {"type": "json_schema", "schema": SCHEMA}})
if msg.stop_reason != "end_turn":
    raise SystemExit(f"Step 1 did not finish (stop_reason={msg.stop_reason}): the chain stops.")

data = json.loads(text_of(msg))
print("Step 1 returns:", data)
reason = gate(data)
if reason:
    print("Gate FAILED:", reason, "-> stop, step 2 is not called.")
else:
    print("Gate passed. Step 2:", step_2(client, data))

valid = {"quantity": "electrode_slope", "value": 98.6, "unit": "%"}
print("\nWith a valid step 1 result", valid)
print("Gate:", gate(valid) or "passed", "-> step 2:", step_2(client, valid))
