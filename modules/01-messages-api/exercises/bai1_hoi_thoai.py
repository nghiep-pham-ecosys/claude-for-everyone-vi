"""Bài 1 — lớp HoiThoai giữ lịch sử nhiều lượt.

Yêu cầu:
- gui(noi_dung) thêm lượt user, gọi self.client.create(...), thêm lượt assistant, trả về text.
- Có system thì truyền tham số `system` (KHÔNG nhét vào messages).
- Lượt assistant phải giữ NGUYÊN msg.content (cả block thinking), không chỉ text.
- Lịch sử chỉ nối thêm: không sửa, không xoá lượt cũ.
- Mỗi lần gọi truyền một list MỚI (bản sao) của lịch sử, để request cũ không bị đổi theo.

Chấm:  CHAM=exercises uv run pytest modules/01-messages-api -q
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
        raise NotImplementedError("TODO: bài 1")
