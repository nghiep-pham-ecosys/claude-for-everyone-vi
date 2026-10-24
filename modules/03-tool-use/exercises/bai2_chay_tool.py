"""Bài 2 — chạy một tool_use thành tool_result.

chay_tool(block, registry) -> dict tool_result
    block: một block tool_use từ msg.content (có .id, .name, .input).
    registry: {tên tool: hàm Python}.

    - Luôn có "type": "tool_result" và "tool_use_id": block.id.
    - Tool không có trong registry -> "is_error": True, content nêu tên tool sai VÀ liệt kê các tool hiện có
      (lời nhắn có ích giúp Claude tự sửa).
    - Hàm ném exception -> "is_error": True, content dạng "TenLoi: thông điệp" (ví dụ "ValueError: ...").
      KHÔNG để exception thoát ra ngoài.
    - Thành công: content là chuỗi; kết quả không phải str thì json.dumps(..., ensure_ascii=False).
      Không có khoá "is_error" (hoặc False).

Chấm:  CHAM=exercises uv run pytest modules/03-tool-use -q
"""
from __future__ import annotations

import json  # noqa: F401
from collections.abc import Callable
from typing import Any


def chay_tool(block: Any, registry: dict[str, Callable[..., Any]]) -> dict[str, Any]:
    raise NotImplementedError("TODO: bài 2")
