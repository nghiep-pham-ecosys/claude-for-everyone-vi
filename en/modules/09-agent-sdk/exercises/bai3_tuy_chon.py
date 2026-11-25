"""Exercise 3: a custom tool, and the options for an agent that runs unattended.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
tuy_chon = options, tao_tool_doi_nhiet = make the temperature conversion tool, doi_nhiet_do = convert
temperature, gia_tri = value, don_vi = unit, tao_options = make the options, chi_doc = read only,
ngan_sach_usd = budget in USD, tra_lich = check the schedule, ghi_nhat_ky = write to the log, ptn = lab.

tao_tool_doi_nhiet(sdk) -> SdkMcpTool
    Use @sdk.tool with the name "doi_nhiet_do", a non-empty description, and an input_schema in JSON Schema form:
      gia_tri: number (required); don_vi: string, enum ["C", "F"] (required), the unit of gia_tri.
    The async handler takes the args dict and returns {"content": [{"type": "text", "text": ...}]}:
      don_vi "C" -> the text "<F> F" with F = C * 9 / 5 + 32, rounded to 1 decimal place (for example "212.0 F").
      don_vi "F" -> the text "<C> C" with C = (F - 32) * 5 / 9, rounded to 1 decimal place (for example "100.0 C").
      any other don_vi -> add "is_error": True, and a text that names both "C" and "F". (With the real SDK, the
      enum stops this before the handler; this branch is a defense, and the test calls the handler directly.)

tao_options(sdk, server, chi_doc, ngan_sach_usd) -> sdk.ClaudeAgentOptions
    - mcp_servers={"ptn": server}; tools=[] (built-in tools off); setting_sources=[]; max_turns=5;
      max_budget_usd=ngan_sach_usd (ngan_sach_usd <= 0: raise ValueError);
      permission_mode="dontAsk" (unattended: a call that is not pre-approved is denied, nobody is asked).
    - chi_doc True:  allowed_tools=["mcp__ptn__tra_lich"], disallowed_tools=["mcp__ptn__ghi_nhat_ky"].
    - chi_doc False: allowed_tools=["mcp__ptn__*"], disallowed_tools=[].

Grade:  CHAM="$PWD/en/modules/09-agent-sdk/exercises" CLAUDE_MOCK=1 uv run pytest modules/09-agent-sdk -q
"""
from __future__ import annotations

from types import ModuleType
from typing import Any


def tao_tool_doi_nhiet(sdk: ModuleType) -> Any:
    raise NotImplementedError("TODO: exercise 3")


def tao_options(sdk: ModuleType, server: dict[str, Any], chi_doc: bool, ngan_sach_usd: float) -> Any:
    raise NotImplementedError("TODO: exercise 3")
