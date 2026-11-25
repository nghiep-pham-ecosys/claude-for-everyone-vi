"""Exercise 1: read the message stream of one agent run.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
tom_tat = summarize, tools_da_goi = tools called, tool_loi = failed tools, so_luot = number of turns,
tra_loi = answer, thanh_cong = succeeded.

tom_tat(sdk, messages) -> dict
    sdk: the SDK module (the mock or claude_agent_sdk); use isinstance(msg, sdk.ResultMessage)... to tell the
    message types apart.
    messages: the list of messages of ONE query() run (read to the end). Return:
    {
      "session_id":   from ResultMessage.session_id,
      "tools_da_goi": the tool names in the order they were called (every ToolUseBlock in the AssistantMessages),
      "tool_loi":     the number of ToolResultBlocks with is_error True (in the UserMessages): this counts both
                      denied calls and tools that failed, so it CANNOT be replaced by len(permission_denials),
      "so_luot":      ResultMessage.num_turns,
      "usd":          ResultMessage.total_cost_usd (it can be None: keep None),
      "tra_loi":      ResultMessage.result as is (the SDK sets it only when subtype is "success"),
      "thanh_cong":   True when subtype == "success" AND is_error is False,
    }
    No ResultMessage at all: raise ValueError.

Grade:  CHAM="$PWD/en/modules/09-agent-sdk/exercises" CLAUDE_MOCK=1 uv run pytest modules/09-agent-sdk -q
"""
from __future__ import annotations

from types import ModuleType
from typing import Any


def tom_tat(sdk: ModuleType, messages: list[Any]) -> dict[str, Any]:
    raise NotImplementedError("TODO: exercise 1")
