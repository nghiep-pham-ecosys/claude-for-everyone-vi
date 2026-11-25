"""Bài 1 — viết một MCP server nhỏ bằng MCPServer (SDK mcp 2.x). (LỜI GIẢI)"""
from __future__ import annotations

from typing import Literal, TypedDict

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

KHONG_TUYET_DOI = {"C": -273.15, "F": -459.67}


class KetQuaNhiet(TypedDict):
    gia_tri: float
    don_vi: str


def tao_may_chu() -> MCPServer:
    server = MCPServer("doi-don-vi")

    @server.tool(annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True))
    def doi_nhiet_do(gia_tri: float, don_vi: Literal["C", "F"]) -> KetQuaNhiet:
        """Đổi nhiệt độ giữa độ C và độ F."""
        if gia_tri < KHONG_TUYET_DOI[don_vi]:
            raise ToolError(f"{gia_tri} {don_vi} thấp hơn độ không tuyệt đối ({KHONG_TUYET_DOI[don_vi]} {don_vi})")
        if don_vi == "C":
            return {"gia_tri": round(gia_tri * 9 / 5 + 32, 1), "don_vi": "F"}
        return {"gia_tri": round((gia_tri - 32) * 5 / 9, 1), "don_vi": "C"}

    @server.resource("dv://don-vi", mime_type="text/plain")
    def don_vi() -> str:
        """Các đơn vị nhiệt độ được hỗ trợ."""
        return "C, F"

    return server
