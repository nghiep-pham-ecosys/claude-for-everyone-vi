"""Module 02: force a format with structured outputs.

People used to prefill "{" to force JSON. On 5.x models prefill returns 400.
The right way: output_config.format with a JSON schema. The API makes sure the text matches the schema
(except when stop_reason is "refusal" or "max_tokens": always check).

Run:  CLAUDE_MOCK=1 uv run python en/modules/02-prompt-engineering/python/04_structured_output.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))

from claude_vi import ClaudeVi, text_of  # noqa: E402

GROUPS = ["teaching", "assessment", "facilities", "other"]
schema = {
    "type": "object",
    "properties": {
        "group": {"type": "string", "enum": GROUPS},
        "severity": {"type": "integer", "description": "1 (minor) to 3 (serious)"},
        "reason": {"type": "string"},
    },
    "required": ["group", "severity", "reason"],
    "additionalProperties": False,  # required with structured outputs
}

msg = ClaudeVi().ask(
    "Classify the feedback: <feedback>The projector in room B2 is blurry; "
    "from the back row you cannot read the slides.</feedback>",
    output_config={"format": {"type": "json_schema", "schema": schema}},
)

if msg.stop_reason != "end_turn":
    raise SystemExit(f"Cannot use the result: stop_reason={msg.stop_reason}")
data = json.loads(text_of(msg))
# The schema cannot set minimum/maximum, so check the value range in code
if not 1 <= data["severity"] <= 3:
    print(f"severity={data['severity']} is outside 1–3 -> handle it (in mock mode it is always 0)")
print(json.dumps(data, ensure_ascii=False, indent=2))
