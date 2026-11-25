"""Exercise 1: a two-step chain with a gate.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
kiem_cong = check the gate, chuoi_hai_buoc = two-step chain, du_lieu = data, van_ban = text,
GIOI_HAN = limits, dai_luong = quantity, gia_tri = value, don_vi = unit, ly_do = reason,
phep_do = measurement, tom_tat = summary, nhiet_do_c = temperature in °C, do_doc_dien_cuc = electrode slope.

kiem_cong(du_lieu) -> None if it passes the gate, otherwise a string with the reason it failed. Check in this order:
    - du_lieu is a dict and has all three fields dai_luong, gia_tri, don_vi;
    - dai_luong is in GIOI_HAN;
    - gia_tri is a number (int or float; a bool does NOT count as a number);
    - don_vi is the unit given in GIOI_HAN;
    - lo <= gia_tri <= hi.
    The gate is code: it does not call Claude.

chuoi_hai_buoc(client, van_ban) -> {"ok", "ly_do", "phep_do", "tom_tat"}
    - Step 1: ONE call client.ask(...) with van_ban, and
      output_config={"format": {"type": "json_schema", "schema": SCHEMA}}.
    - stop_reason other than "end_turn", or broken JSON -> ok False, ly_do not empty, do NOT call step 2.
    - The gate fails -> ok False, ly_do is the reason from kiem_cong, phep_do is the extracted dict,
      do NOT call step 2.
    - The gate passes -> step 2: one call that writes a summary sentence; ok True, ly_do None,
      tom_tat is text_of(step 2).
    The test counts the calls: calling step 2 after the gate fails is a failed exercise.

Grade:  CHAM="$PWD/en/modules/08-agents-workflows/exercises" uv run pytest modules/08-agents-workflows -q
"""
from __future__ import annotations

from typing import Any

from claude_vi import ClaudeVi

# The valid range and unit of each quantity (made-up numbers)
GIOI_HAN = {
    "pH": (0.0, 14.0, ""),
    "nhiet_do_c": (-10.0, 60.0, "°C"),
    "do_doc_dien_cuc": (80.0, 120.0, "%"),
}
SCHEMA = {
    "type": "object",
    "properties": {
        "dai_luong": {"type": "string", "enum": list(GIOI_HAN)},
        "gia_tri": {"type": "number"},
        "don_vi": {"type": "string"},
    },
    "required": ["dai_luong", "gia_tri", "don_vi"],
    "additionalProperties": False,
}


def kiem_cong(du_lieu: Any) -> str | None:
    raise NotImplementedError("TODO: exercise 1, the gate")


def chuoi_hai_buoc(client: ClaudeVi, van_ban: str) -> dict[str, Any]:
    raise NotImplementedError("TODO: exercise 1, the two-step chain")
