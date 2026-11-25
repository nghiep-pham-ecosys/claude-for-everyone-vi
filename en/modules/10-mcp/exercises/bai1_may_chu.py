"""Exercise 1: write a small MCP server with MCPServer (SDK mcp 2.x).

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
tao_may_chu = make the server, doi_nhiet_do = convert the temperature, gia_tri = value, don_vi = unit,
KetQuaNhiet = temperature result, "doi-don-vi" = "convert-units".

tao_may_chu() -> MCPServer   (server name: "doi-don-vi")
    Tool "doi_nhiet_do":
      - parameters gia_tri: float; don_vi: Literal["C", "F"] (the unit of gia_tri) -> inputSchema has the enum
        ["C", "F"].
      - returns KetQuaNhiet (TypedDict: gia_tri: float, don_vi: str) -> the tool has an outputSchema and
        structured_content:
          "C" -> {"gia_tri": round(gia_tri * 9 / 5 + 32, 1), "don_vi": "F"}
          "F" -> {"gia_tri": round((gia_tri - 32) * 5 / 9, 1), "don_vi": "C"}
      - below absolute zero (gia_tri < -273.15 for "C", < -459.67 for "F"): raise ToolError with a message that
        contains the Vietnamese words "độ không tuyệt đối" ("absolute zero"; the shared test looks for them).
        The client gets is_error=True with the message.
      - annotations: read_only_hint=True, idempotent_hint=True.
      - the function's docstring is not empty (it becomes the tool's description).
    Resource "dv://don-vi" (mime_type "text/plain"): returns the string "C, F".

Grade:  CHAM="$PWD/en/modules/10-mcp/exercises" CLAUDE_MOCK=1 uv run pytest modules/10-mcp -q
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
    raise NotImplementedError("TODO: exercise 1")
