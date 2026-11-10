"""Bài 3 — hội thoại append-only, thêm chỉ dẫn không sửa system. (LỜI GIẢI)"""
from __future__ import annotations

import copy
from typing import Any

from claude_vi import ClaudeVi, text_of


class HoiThoai:
    def __init__(self, client: ClaudeVi, system: str) -> None:
        self.client = client
        self._system = system
        self.messages: list[dict[str, Any]] = []
        self._cho: list[str] = []

    @property
    def system(self) -> str:
        return self._system

    def them_chi_dan(self, chi_dan: str) -> None:
        if not chi_dan.strip():
            raise ValueError("Chỉ dẫn rỗng")
        self._cho.append(chi_dan)

    def gui(self, noi_dung: str) -> str:
        self.messages.append({"role": "user", "content": noi_dung})
        if self._cho:
            self.messages.append({"role": "system", "content": "\n".join(self._cho)})
            self._cho = []
        msg = self.client.create(system=self._system, messages=list(self.messages))
        self.messages.append({"role": "assistant", "content": msg.content})
        return text_of(msg)

    def luu(self) -> dict[str, Any]:
        return {"system": self._system, "messages": copy.deepcopy(self.messages)}
