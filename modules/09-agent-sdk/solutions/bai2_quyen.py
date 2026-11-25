"""Bài 2 — chính sách quyền: can_use_tool và hook PreToolUse. (LỜI GIẢI)"""
from __future__ import annotations

from types import ModuleType
from typing import Any

GHI = "mcp__ptn__ghi_nhat_ky"
TU_CAM = ("xoá", "xóa", "huỷ", "hủy")


def tao_can_use_tool(sdk: ModuleType, cho_phep_ghi: bool):
    async def can_use_tool(tool_name: str, input_data: dict[str, Any], context: Any):
        if tool_name.startswith("mcp__ptn__tra_"):
            return sdk.PermissionResultAllow()
        if tool_name == GHI and cho_phep_ghi:
            noi_dung = str(input_data.get("noi_dung", ""))
            if len(noi_dung) <= 200:
                return sdk.PermissionResultAllow(updated_input={"noi_dung": f"[agent] {noi_dung}"})
            return sdk.PermissionResultDeny(message="Nội dung nhật ký dài quá 200 ký tự.")
        return sdk.PermissionResultDeny(message=f"Không được dùng {tool_name}.")
    return can_use_tool


def _chuoi(x: Any) -> list[str]:
    if isinstance(x, str):
        return [x]
    if isinstance(x, dict):
        return [s for v in x.values() for s in _chuoi(v)]
    if isinstance(x, list):
        return [s for v in x for s in _chuoi(v)]
    return []


async def hook_chi_them(input_data: dict[str, Any], tool_use_id: str | None, context: Any) -> dict[str, Any]:
    chu = " ".join(_chuoi(input_data.get("tool_input") or {})).lower()
    if any(t in chu for t in TU_CAM):
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                       "permissionDecisionReason": "Nhật ký chỉ được thêm, không xoá hay huỷ."}}
    return {}
