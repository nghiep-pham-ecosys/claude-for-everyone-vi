"""Exercise 2: a permission policy with can_use_tool and a PreToolUse hook.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
quyen = permissions, tao_can_use_tool = make a can_use_tool callback, cho_phep_ghi = allow writing,
hook_chi_them = append-only hook, tra_lich = check the schedule, ghi_nhat_ky = write to the log,
noi_dung = content, ptn = lab.

The tools of this exercise (server key "ptn"): mcp__ptn__tra_lich (read only), mcp__ptn__ghi_nhat_ky (has a
side effect).

tao_can_use_tool(sdk, cho_phep_ghi) -> async callback (tool_name, input_data, context) -> PermissionResult
    - A tool name that starts with "mcp__ptn__tra_": sdk.PermissionResultAllow() (input unchanged).
    - mcp__ptn__ghi_nhat_ky: allow when cho_phep_ghi is True AND input_data["noi_dung"] is at most 200 characters
      long; when you allow it, return updated_input={"noi_dung": "[agent] " + the original noi_dung}.
    - Every other case: sdk.PermissionResultDeny with a NON-empty message (Claude reads this reason).
    - Do not change the input_data dict you were given.

hook_chi_them(input_data, tool_use_id, context) -> dict   (an async callback for the PreToolUse event)
    - input_data["tool_input"] (a dict) contains one of the words "xoá", "xóa", "huỷ", "hủy" (Vietnamese for
      "delete" and "cancel", in either spelling; any case, in any string value): return
      {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                              "permissionDecisionReason": <a non-empty reason>}}
    - Otherwise: return {} (no opinion).

Grade:  CHAM="$PWD/en/modules/09-agent-sdk/exercises" CLAUDE_MOCK=1 uv run pytest modules/09-agent-sdk -q
"""
from __future__ import annotations

from types import ModuleType
from typing import Any


def tao_can_use_tool(sdk: ModuleType, cho_phep_ghi: bool):
    raise NotImplementedError("TODO: exercise 2")


async def hook_chi_them(input_data: dict[str, Any], tool_use_id: str | None, context: Any) -> dict[str, Any]:
    raise NotImplementedError("TODO: exercise 2")
