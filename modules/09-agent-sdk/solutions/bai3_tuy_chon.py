"""Bài 3 — tool tự viết và options cho một agent chạy không người canh. (LỜI GIẢI)"""
from __future__ import annotations

from types import ModuleType
from typing import Any


def tao_tool_doi_nhiet(sdk: ModuleType) -> Any:
    @sdk.tool("doi_nhiet_do", "Đổi nhiệt độ giữa độ C và độ F.", {
        "type": "object",
        "properties": {"gia_tri": {"type": "number"}, "don_vi": {"type": "string", "enum": ["C", "F"]}},
        "required": ["gia_tri", "don_vi"],
    })
    async def doi_nhiet_do(args: dict[str, Any]) -> dict[str, Any]:
        v, don_vi = float(args["gia_tri"]), args.get("don_vi")
        if don_vi == "C":
            return {"content": [{"type": "text", "text": f"{round(v * 9 / 5 + 32, 1)} F"}]}
        if don_vi == "F":
            return {"content": [{"type": "text", "text": f"{round((v - 32) * 5 / 9, 1)} C"}]}
        return {"content": [{"type": "text", "text": f"Đơn vị '{don_vi}' không hợp lệ. Dùng C hoặc F."}],
                "is_error": True}
    return doi_nhiet_do


def tao_options(sdk: ModuleType, server: dict[str, Any], chi_doc: bool, ngan_sach_usd: float) -> Any:
    if ngan_sach_usd <= 0:
        raise ValueError("Ngân sách phải dương")
    return sdk.ClaudeAgentOptions(
        mcp_servers={"ptn": server}, tools=[], setting_sources=[], max_turns=5, max_budget_usd=ngan_sach_usd,
        permission_mode="dontAsk",
        allowed_tools=["mcp__ptn__tra_lich"] if chi_doc else ["mcp__ptn__*"],
        disallowed_tools=["mcp__ptn__ghi_nhat_ky"] if chi_doc else [],
    )
