"""Exercise 1: a HoiThoai ("conversation") class that keeps a multi-turn history.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
HoiThoai = conversation, gui = send, noi_dung = content, lich_su = history.

Task:
- gui(noi_dung) adds a user turn, calls self.client.create(...), adds the assistant turn, and returns the text.
- If there is a system prompt, pass it in the `system` parameter (do NOT put it in messages).
- The assistant turn must keep msg.content UNCHANGED (thinking blocks included), not just the text.
- The history is append-only: never edit or delete an old turn.
- Each call passes a NEW list (a copy) of the history, so an old request does not change later.

Grade:  CHAM="$PWD/en/modules/01-messages-api/exercises" uv run pytest modules/01-messages-api -q
"""
from __future__ import annotations

from typing import Any

from claude_vi import ClaudeVi, text_of  # noqa: F401


class HoiThoai:
    def __init__(self, client: ClaudeVi, system: str | None = None) -> None:
        self.client = client
        self.system = system
        self.lich_su: list[dict[str, Any]] = []

    def gui(self, noi_dung: str) -> str:
        raise NotImplementedError("TODO: exercise 1")
