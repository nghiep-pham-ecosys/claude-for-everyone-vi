"""Module 09: who may run which tool (quyen_va_hook = permissions and hooks): allowed_tools, can_use_tool and
the PreToolUse hook.

The order in which the SDK decides on a tool call (docs Permissions): hook -> deny rules (disallowed_tools)
-> ask rules -> permission_mode -> allow rules (allowed_tools) -> can_use_tool. If nobody approves, the call
is denied. A call that allowed_tools already approved does NOT reach can_use_tool: to see every call, use a
PreToolUse hook.

Run:  CLAUDE_MOCK=1 uv run python en/modules/09-agent-sdk/python/02_quyen_va_hook.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cong_cu import NHAT_KY, doc_het, nap_sdk, options_co_ban, tao_server, ten_day_du  # noqa: E402

CHECK_SCHEDULE, WRITE_LOG = ten_day_du("tra_lich"), ten_day_du("ghi_nhat_ky")
BANNED_WORDS = ("delete", "cancel")


run = doc_het


def summarize(sdk, messages: list) -> None:
    for msg in messages:
        if isinstance(msg, sdk.UserMessage):
            for b in msg.content:
                if isinstance(b, sdk.ToolResultBlock):
                    print(f"   {'DENIED/ERROR' if b.is_error else 'ran':<12} {str(b.content)[:80]}")
        if isinstance(msg, sdk.ResultMessage):
            print(f"   result {msg.subtype}")


def make_can_use_tool(sdk, asked_for: list):
    """can_use_tool: asked only when no other rule decides. Here: approve writing to the log if the text is short."""
    async def can_use_tool(tool_name: str, input_data: dict, context):
        asked_for.append(tool_name)
        if tool_name == WRITE_LOG and len(input_data.get("noi_dung", "")) <= 200:
            # updated_input: you can change the input before the tool runs, for example add a source label
            return sdk.PermissionResultAllow(updated_input={"noi_dung": f"[agent] {input_data['noi_dung']}"})
        return sdk.PermissionResultDeny(message=f"{tool_name} not approved: the text is too long, or the tool "
                                                "is unknown.")
    return can_use_tool


async def hook_block_banned_words(input_data: dict, tool_use_id, context) -> dict:
    """PreToolUse: runs for EVERY call that matches the matcher, even a call that allowed_tools approved."""
    content = str(input_data.get("tool_input", {})).lower()
    if any(w in content for w in BANNED_WORDS):
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                       "permissionDecisionReason": "The log is append only: no delete, "
                                                                   "no cancel."}}
    return {}  # no opinion: continue down the permission flow


async def main() -> None:
    sdk = nap_sdk()
    NHAT_KY.unlink(missing_ok=True)
    server = {"ptn": tao_server(sdk)}

    print("1) allowed_tools only for tra_lich: nobody approves ghi_nhat_ky -> denied")
    summarize(sdk, await run(sdk, "Check the HV-200 schedule, then write it to the log.", options_co_ban(
        sdk, mcp_servers=server, allowed_tools=[CHECK_SCHEDULE])))

    print("\n2) Add can_use_tool: it is asked ONLY for ghi_nhat_ky (allowed_tools already approved tra_lich)")
    asked_for: list = []
    summarize(sdk, await run(sdk, "Check the HV-200 schedule, then write it to the log.", options_co_ban(
        sdk, mcp_servers=server, allowed_tools=[CHECK_SCHEDULE], can_use_tool=make_can_use_tool(sdk, asked_for))))
    print(f"   can_use_tool was asked for: {asked_for}")
    if NHAT_KY.exists():
        print(f"   log book: {NHAT_KY.read_text('utf-8').strip()}")

    print("\n3) A PreToolUse hook blocks by content, even for tools that are in allowed_tools")
    hooks = {"PreToolUse": [sdk.HookMatcher(matcher="^mcp__ptn__", hooks=[hook_block_banned_words])]}
    summarize(sdk, await run(sdk, "Delete the QS-3 booking and log the deletion.", options_co_ban(
        sdk, mcp_servers=server, allowed_tools=["mcp__ptn__*"], hooks=hooks)))
    print("   The matcher compares only the tool NAME (an exact name, or a regex like here); filtering by content"
          "\n   must happen in the callback.")


if __name__ == "__main__":
    asyncio.run(main())
