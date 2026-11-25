"""Exercise 2: a router by enum label, with a fallback branch.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
dinh_tuyen = route, cau_hoi = question, xu_ly = handlers, du_phong = fallback, nhan = label,
ket_qua = result. The labels: khac = other, quy_trinh = procedure, so_lieu = data (readings).

dinh_tuyen(client, cau_hoi, xu_ly, du_phong) -> (nhan, ket_qua)
    - ONE classification call: client.ask(cau_hoi, system=SYSTEM,
      output_config={"format": {"type": "json_schema", "schema": SCHEMA}}).
      The user turn holds only the question; the classification instructions are in SYSTEM.
    - Read the label from the JSON (key "nhan"). If the label is in xu_ly -> return (nhan, xu_ly[nhan](cau_hoi)).
    - Every other case -> ("du_phong", du_phong(cau_hoi)):
      stop_reason other than "end_turn", broken JSON, a missing key, an unknown label, or a valid label
      with no function in xu_ly yet.
    - Do not call Claude again: the handler decides for itself whether to make a call.

The mock does not understand the question: it picks the label whose keyword is in the question, or else the
first label ("khac").

Grade:  CHAM="$PWD/en/modules/08-agents-workflows/exercises" uv run pytest modules/08-agents-workflows -q
"""
from __future__ import annotations

from collections.abc import Callable

from claude_vi import ClaudeVi

NHAN = ["khac", "quy_trinh", "so_lieu"]
SCHEMA = {"type": "object", "properties": {"nhan": {"type": "string", "enum": NHAN}},
          "required": ["nhan"], "additionalProperties": False}
SYSTEM = (
    "Classify the question of a lab user. quy_trinh: asks how to do something, the steps, a device error code. "
    "so_lieu: asks for a current environmental reading. khac: everything else."
)


def dinh_tuyen(client: ClaudeVi, cau_hoi: str, xu_ly: dict[str, Callable[[str], str]],
               du_phong: Callable[[str], str]) -> tuple[str, str]:
    raise NotImplementedError("TODO: exercise 2")
