"""Bài 1 — viết một MCP server nhỏ bằng MCPServer (SDK mcp 2.x).

tao_may_chu() -> MCPServer   (tên server: "doi-don-vi")
    Tool "doi_nhiet_do":
      - tham số gia_tri: float; don_vi: Literal["C", "F"] (đơn vị của gia_tri) -> inputSchema có enum ["C", "F"].
      - trả KetQuaNhiet (TypedDict: gia_tri: float, don_vi: str) -> tool có outputSchema và structured_content:
          "C" -> {"gia_tri": round(gia_tri * 9 / 5 + 32, 1), "don_vi": "F"}
          "F" -> {"gia_tri": round((gia_tri - 32) * 5 / 9, 1), "don_vi": "C"}
      - dưới độ không tuyệt đối (gia_tri < -273.15 với "C", < -459.67 với "F"): raise ToolError với lời nhắn có
        cụm "độ không tuyệt đối" (client nhận is_error=True kèm lời nhắn).
      - annotations: read_only_hint=True, idempotent_hint=True.
      - docstring của hàm khác rỗng (thành description của tool).
    Resource "dv://don-vi" (mime_type "text/plain"): trả chuỗi "C, F".

Chấm:  CHAM=exercises CLAUDE_MOCK=1 uv run pytest modules/10-mcp -q
"""
from __future__ import annotations

from typing import Literal, TypedDict  # noqa: F401

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError  # noqa: F401
from mcp.types import ToolAnnotations  # noqa: F401


class KetQuaNhiet(TypedDict):
    gia_tri: float
    don_vi: str


def tao_may_chu() -> MCPServer:
    raise NotImplementedError("TODO: bài 1")
