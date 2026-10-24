"""Bài 1 — lớp HoiThoai giữ lịch sử nhiều lượt. (LỜI GIẢI)"""
from __future__ import annotations

from typing import Any

from claude_vi import ClaudeVi, text_of


class HoiThoai:
    def __init__(self, client: ClaudeVi, system: str | None = None) -> None:
        self.client = client
        self.system = system
        self.lich_su: list[dict[str, Any]] = []

    def gui(self, noi_dung: str) -> str:
        self.lich_su.append({"role": "user", "content": noi_dung})
        params: dict[str, Any] = {"messages": list(self.lich_su)}
        if self.system:
            params["system"] = self.system
        msg = self.client.create(**params)
        self.lich_su.append({"role": "assistant", "content": msg.content})
        return text_of(msg)
