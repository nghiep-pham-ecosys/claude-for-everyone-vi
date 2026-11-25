"""Exercise 1: define a strict tool.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
tao_tool = build a tool, ten = name, mo_ta = description, thuoc_tinh = properties, bat_buoc = required.

tao_tool(ten, mo_ta, thuoc_tinh, bat_buoc) -> dict with the tool definition
    - ten must match ^[a-zA-Z0-9_-]{1,128}$ (no accented letters, no spaces) -> otherwise ValueError.
    - mo_ta: the docs say a detailed description is the MOST IMPORTANT factor, so write at least 3–4 sentences.
      Here: fewer than 3 periods -> ValueError.
    - Every name in bat_buoc must be in thuoc_tinh -> otherwise ValueError.
    - The result:
        {"name": ten, "description": mo_ta, "strict": True,
         "input_schema": {"type": "object", "properties": thuoc_tinh,
                          "required": bat_buoc, "additionalProperties": False}}

Grade:  CHAM="$PWD/en/modules/03-tool-use/exercises" uv run pytest modules/03-tool-use -q
"""
from __future__ import annotations

from typing import Any


def tao_tool(ten: str, mo_ta: str, thuoc_tinh: dict[str, dict[str, Any]], bat_buoc: list[str]) -> dict[str, Any]:
    raise NotImplementedError("TODO: exercise 1")
