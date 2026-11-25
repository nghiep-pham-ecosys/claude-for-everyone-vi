"""Bài 3 — host quyết định duyệt và trả kết quả tool MCP cho Claude.

can_duyet(tool, cho_chay) -> bool      (True = phải hỏi người dùng trước khi gọi)
    tool: mcp.types.Tool; cho_chay: tập tên tool mà HOST cho chạy không cần hỏi.
    - tool.name không thuộc cho_chay: True, BẤT KỂ annotation (annotation của server không đáng tin).
    - tool.name thuộc cho_chay nhưng annotation có destructive_hint là True (giá trị khai RÕ): True. Luật của
      bài: với server chưa được tin, annotation chỉ được làm host thận trọng hơn. Thiếu annotation hay
      destructive_hint là None thì bỏ qua: host đã tự tin các tool trong cho_chay (dù spec coi
      destructiveHint mặc định là true).
    - còn lại: False.

sang_tool_result(tool_use_id, ket_qua) -> dict   (ket_qua: mcp.types.CallToolResult)
    {"type": "tool_result", "tool_use_id": ..., "is_error": bool(ket_qua.is_error), "content": [...]}
    content: mỗi block type "text" của ket_qua.content thành {"type": "text", "text": ...} (giữ thứ tự, bỏ mọi
    block khác như image, audio, resource; đừng đọc c.text của block không phải text). Không có block text nào mà structured_content khác None: một block text là
    json.dumps(structured_content, ensure_ascii=False) (kể cả khi structured_content là {} hay rỗng khác). Không có gì: một block text "(không có nội dung)".

Chấm:  CHAM=exercises CLAUDE_MOCK=1 uv run pytest modules/10-mcp -q
"""
from __future__ import annotations

from typing import Any


def can_duyet(tool: Any, cho_chay: set[str]) -> bool:
    raise NotImplementedError("TODO: bài 3")


def sang_tool_result(tool_use_id: str, ket_qua: Any) -> dict[str, Any]:
    raise NotImplementedError("TODO: bài 3")
