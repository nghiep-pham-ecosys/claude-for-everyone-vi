"""Module 05: a schema written with Pydantic, with the constraints checked in code.

Structured outputs do not accept minimum/maximum. anthropic.transform_schema() drops those constraints
from the schema it sends and copies them into the description. You still keep the constraints on your side:
Pydantic checks them again when it reads the result.

Run:  CLAUDE_MOCK=1 uv run python en/modules/05-structured-pdf-citations/python/01_pydantic_schema.py
"""
import json
import sys
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))

from anthropic import transform_schema  # noqa: E402
from claude_vi import ClaudeVi, text_of  # noqa: E402
from pydantic import BaseModel, Field, ValidationError  # noqa: E402


class Measurement(BaseModel):
    sample: str = Field(description="sample code, for example W1")
    quantity: Literal["pH", "DO", "turbidity"]
    value: float = Field(ge=0)
    unit: str = Field(description="the unit as written in the text; an empty string if there is none")
    note: str | None = None             # optional + union: counts toward the 24 optional / 16 union limits


class Table(BaseModel):
    measurements: list[Measurement]


schema = transform_schema(Table)
print("Schema sent (ge=0 has moved into the description):")
print(json.dumps(schema["$defs"]["Measurement"]["properties"]["value"], ensure_ascii=False))

msg = ClaudeVi().ask(
    "<text>Sample W1: pH 7.1; DO 6.2 mg/L. Sample W2: turbidity 12 NTU.</text>\n"
    "Put each measurement on its own row.",
    output_config={"format": {"type": "json_schema", "schema": schema}},
)
if msg.stop_reason != "end_turn":
    raise SystemExit(f"The result cannot be used: stop_reason={msg.stop_reason}")

try:
    table = Table.model_validate_json(text_of(msg))   # also checks ge=0, which the API does not guarantee
except ValidationError as e:
    raise SystemExit(f"The JSON matches the schema but breaks your own constraints:\n{e}") from None
for m in table.measurements:
    print(m)
