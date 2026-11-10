"""Bài 3 — hội thoại append-only, thêm chỉ dẫn mà không sửa system.

Mock của repo chạy prefix check như API: sửa system hay lượt cũ rồi gửi lại block thinking -> 400.

class HoiThoai(client, system)
    system         chỉ đọc (property): không có cách nào đổi system sau khi tạo.
    messages       danh sách message đã gửi/nhận, chỉ nối thêm.

    them_chi_dan(chi_dan)
        Ghi nhận chỉ dẫn mới (ví dụ "từ giờ trả lời bằng tiếng Anh"). Chưa gửi gì.
        chi_dan rỗng (sau strip) -> raise ValueError.
    gui(noi_dung) -> str
        1. Nối {"role": "user", "content": noi_dung}.
        2. Nếu có chỉ dẫn đang chờ: nối MỘT message {"role": "system", "content": ...} ngay sau lượt user đó
           (nhiều chỉ dẫn thì nối bằng "\\n"), rồi xoá hàng chờ. Message system phải đứng ngay sau lượt user
           và trước lượt assistant — sai chỗ là 400.
        3. Gọi client.create(system=<system ban đầu>, messages=...).
        4. Nối {"role": "assistant", "content": msg.content} NGUYÊN VẸN. Trả text_of(msg).
    luu() -> {"system": ..., "messages": bản sao sâu của messages}
        Để lưu phiên và chạy tiếp sau: phát lại đúng những gì đã gửi, không dựng lại từ template.

Chấm:  CHAM=exercises uv run pytest modules/07-thinking -q
"""
from __future__ import annotations

import copy  # noqa: F401
from typing import Any

from claude_vi import ClaudeVi, text_of  # noqa: F401


class HoiThoai:
    def __init__(self, client: ClaudeVi, system: str) -> None:
        raise NotImplementedError("TODO: bài 3")

    @property
    def system(self) -> str:
        raise NotImplementedError("TODO: bài 3")

    def them_chi_dan(self, chi_dan: str) -> None:
        raise NotImplementedError("TODO: bài 3")

    def gui(self, noi_dung: str) -> str:
        raise NotImplementedError("TODO: bài 3")

    def luu(self) -> dict[str, Any]:
        raise NotImplementedError("TODO: bài 3")
