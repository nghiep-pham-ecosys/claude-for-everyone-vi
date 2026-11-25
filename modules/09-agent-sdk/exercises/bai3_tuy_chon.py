"""Bài 3 — tool tự viết và options cho một agent chạy không người canh.

tao_tool_doi_nhiet(sdk) -> SdkMcpTool
    Dùng @sdk.tool với tên "doi_nhiet_do", mô tả khác rỗng, input_schema dạng JSON Schema:
      gia_tri: number (bắt buộc); don_vi: string, enum ["C", "F"] (bắt buộc) — đơn vị của gia_tri.
    Handler async nhận dict args, trả {"content": [{"type": "text", "text": ...}]}:
      don_vi "C" -> text "<F> F" với F = C * 9 / 5 + 32, làm tròn 1 chữ số thập phân (ví dụ "212.0 F").
      don_vi "F" -> text "<C> C" với C = (F - 32) * 5 / 9, làm tròn 1 chữ số (ví dụ "100.0 C").
      don_vi khác -> thêm "is_error": True và text nêu cả "C" và "F". (Với SDK thật, enum đã chặn trước handler;
      nhánh này là phòng thủ và test gọi thẳng handler để chấm.)

tao_options(sdk, server, chi_doc, ngan_sach_usd) -> sdk.ClaudeAgentOptions
    - mcp_servers={"ptn": server}; tools=[] (tắt tool dựng sẵn); setting_sources=[]; max_turns=5;
      max_budget_usd=ngan_sach_usd (ngan_sach_usd <= 0: raise ValueError);
      permission_mode="dontAsk" (không người canh: lời gọi chưa được duyệt sẵn thì bị từ chối, không hỏi ai).
    - chi_doc True:  allowed_tools=["mcp__ptn__tra_lich"], disallowed_tools=["mcp__ptn__ghi_nhat_ky"].
    - chi_doc False: allowed_tools=["mcp__ptn__*"], disallowed_tools=[].

Chấm:  CHAM=exercises CLAUDE_MOCK=1 uv run pytest modules/09-agent-sdk -q
"""
from __future__ import annotations

from types import ModuleType
from typing import Any


def tao_tool_doi_nhiet(sdk: ModuleType) -> Any:
    raise NotImplementedError("TODO: bài 3")


def tao_options(sdk: ModuleType, server: dict[str, Any], chi_doc: bool, ngan_sach_usd: float) -> Any:
    raise NotImplementedError("TODO: bài 3")
