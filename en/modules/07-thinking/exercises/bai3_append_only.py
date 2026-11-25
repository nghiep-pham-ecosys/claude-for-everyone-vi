"""Exercise 3: an append-only conversation; add instructions without changing system.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
HoiThoai = conversation, them_chi_dan = add an instruction, chi_dan = instruction, gui = send,
noi_dung = content, luu = save.

This repo's mock runs the prefix check like the API: change system or an old turn, then send a thinking
block back -> 400.

class HoiThoai(client, system)
    system         read-only (a property): there is no way to change system after it is created.
    messages       the list of messages sent and received, only ever appended to.

    them_chi_dan(chi_dan)
        Record a new instruction (for example "from now on, answer in Vietnamese"). Send nothing yet.
        chi_dan empty (after strip) -> raise ValueError.
    gui(noi_dung) -> str
        1. Append {"role": "user", "content": noi_dung}.
        2. If instructions are waiting: append ONE message {"role": "system", "content": ...} right after
           that user turn (several instructions are joined with "\\n"), then clear the queue. The system
           message must come right after the user turn and before the assistant turn; in the wrong place it is a 400.
        3. Call client.create(system=<the original system>, messages=...).
        4. Append {"role": "assistant", "content": msg.content} UNCHANGED. Return text_of(msg).
    luu() -> {"system": ..., "messages": a deep copy of messages}
        To save the session and go on later: replay exactly what was sent; do not rebuild it from a template.

Grade:  CHAM="$PWD/en/modules/07-thinking/exercises" uv run pytest modules/07-thinking -q
"""
from __future__ import annotations

import copy  # noqa: F401
from typing import Any

from claude_vi import ClaudeVi, text_of  # noqa: F401


class HoiThoai:
    def __init__(self, client: ClaudeVi, system: str) -> None:
        raise NotImplementedError("TODO: exercise 3")

    @property
    def system(self) -> str:
        raise NotImplementedError("TODO: exercise 3")

    def them_chi_dan(self, chi_dan: str) -> None:
        raise NotImplementedError("TODO: exercise 3")

    def gui(self, noi_dung: str) -> str:
        raise NotImplementedError("TODO: exercise 3")

    def luu(self) -> dict[str, Any]:
        raise NotImplementedError("TODO: exercise 3")
