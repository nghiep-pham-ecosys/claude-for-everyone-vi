"""Bài 1 — đọc luồng message của một lần chạy agent.

tom_tat(sdk, messages) -> dict
    sdk: module SDK (mock hoặc claude_agent_sdk); dùng isinstance(msg, sdk.ResultMessage)... để nhận loại message.
    messages: list message của MỘT lần query() (đã đọc hết). Trả về:
    {
      "session_id":   từ ResultMessage.session_id,
      "tools_da_goi": tên tool theo thứ tự gọi (mọi ToolUseBlock trong các AssistantMessage),
      "tool_loi":     số ToolResultBlock có is_error là True (trong các UserMessage): gồm cả lời gọi bị từ chối
                      lẫn tool chạy lỗi, nên KHÔNG thay được bằng len(permission_denials),
      "so_luot":      ResultMessage.num_turns,
      "usd":          ResultMessage.total_cost_usd (có thể None: giữ None),
      "tra_loi":      ResultMessage.result nguyên văn (SDK chỉ đặt khi subtype là "success"),
      "thanh_cong":   True khi subtype == "success" VÀ is_error là False,
    }
    Không có ResultMessage nào: raise ValueError.

Chấm:  CHAM=exercises CLAUDE_MOCK=1 uv run pytest modules/09-agent-sdk -q
"""
from __future__ import annotations

from types import ModuleType
from typing import Any


def tom_tat(sdk: ModuleType, messages: list[Any]) -> dict[str, Any]:
    raise NotImplementedError("TODO: bài 1")
