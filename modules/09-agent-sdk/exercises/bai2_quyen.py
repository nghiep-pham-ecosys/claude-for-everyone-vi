"""Bài 2 — chính sách quyền: can_use_tool và hook PreToolUse.

Tool của bài (server khoá "ptn"): mcp__ptn__tra_lich (chỉ đọc), mcp__ptn__ghi_nhat_ky (có tác dụng phụ).

tao_can_use_tool(sdk, cho_phep_ghi) -> callback async (tool_name, input_data, context) -> PermissionResult
    - Tên tool bắt đầu bằng "mcp__ptn__tra_": sdk.PermissionResultAllow() (không sửa input).
    - mcp__ptn__ghi_nhat_ky: cho phép khi cho_phep_ghi là True VÀ input_data["noi_dung"] dài tối đa 200 ký tự;
      khi cho phép, trả updated_input={"noi_dung": "[agent] " + noi_dung gốc}.
    - Mọi trường hợp khác: sdk.PermissionResultDeny với message KHÁC rỗng (Claude đọc lý do này).
    - Không sửa dict input_data được truyền vào.

hook_chi_them(input_data, tool_use_id, context) -> dict   (callback async cho sự kiện PreToolUse)
    - input_data["tool_input"] (dict) có chứa một trong các từ "xoá", "xóa", "huỷ", "hủy" (không phân biệt hoa
      thường, ở bất kỳ giá trị chuỗi nào): trả
      {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                              "permissionDecisionReason": <lý do khác rỗng>}}
    - Ngược lại: trả {} (không ý kiến).

Chấm:  CHAM=exercises CLAUDE_MOCK=1 uv run pytest modules/09-agent-sdk -q
"""
from __future__ import annotations

from types import ModuleType
from typing import Any


def tao_can_use_tool(sdk: ModuleType, cho_phep_ghi: bool):
    raise NotImplementedError("TODO: bài 2")


async def hook_chi_them(input_data: dict[str, Any], tool_use_id: str | None, context: Any) -> dict[str, Any]:
    raise NotImplementedError("TODO: bài 2")
