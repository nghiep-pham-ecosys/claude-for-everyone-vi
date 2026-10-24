"""Kiểm tra request theo luật của từng model, TRƯỚC khi gửi.

Mục đích: mock mode phải "đau" giống API thật. Nếu notebook dùng
temperature trên Haiku 5.5, CI phải đỏ chứ không được xanh giả.
"""
from __future__ import annotations

from typing import Any

from .config import load_models

SAMPLING_PARAMS = ("temperature", "top_p", "top_k")


class ModelRuleError(ValueError):
    """Request sẽ bị API trả 400. Thông báo bằng tiếng Việt kèm cách sửa."""


def check_request(params: dict[str, Any]) -> None:
    cfg = load_models()["models"]
    model = params.get("model")
    if model not in cfg:
        raise ModelRuleError(
            f"Model '{model}' không có trong config/models.yaml. "
            "Thêm vào allowlist hoặc dùng CLAUDE_MODEL hợp lệ."
        )
    entry = cfg[model]
    status = entry.get("status")
    if status == "retired":
        raise ModelRuleError(f"'{model}' đã ngừng hoạt động ({entry.get('retired_on')}).")

    rules = entry.get("rules", {})
    errors: list[str] = []

    if not rules.get("sampling_params_allowed", True):
        used = [p for p in SAMPLING_PARAMS if p in params]
        if used:
            errors.append(
                f"{', '.join(used)} không được hỗ trợ trên {model}. "
                "Bỏ tham số này; điều khiển độ sâu suy nghĩ bằng output_config.effort."
            )

    thinking = params.get("thinking") or {}
    if thinking.get("type") == "enabled" and "budget_tokens" in thinking:
        errors.append(
            "budget_tokens (extended thinking thủ công) đã bị bỏ trên model 5.x. "
            "Dùng adaptive thinking + output_config.effort."
        )
    if thinking.get("type") == "disabled" and not rules.get("thinking_disabled_allowed", True):
        hint = ' Thử thinking={"type": "between_tools"}.' if model == "claude-sonnet-5-5" else ""
        errors.append(f"Không tắt được thinking trên {model}.{hint}")

    tool_choice = params.get("tool_choice") or {}
    if tool_choice.get("type") in ("any", "tool") and not rules.get("forced_tool_choice_allowed", True):
        errors.append(
            f"tool_choice '{tool_choice['type']}' trả 400 trên {model}. "
            "Dùng tool_choice auto + strict tool use, hoặc structured outputs."
        )

    messages = params.get("messages") or []
    if messages and messages[-1].get("role") == "assistant" and not rules.get("assistant_prefill_allowed", True):
        errors.append(
            f"Prefill tin nhắn assistant không được hỗ trợ trên {model}. "
            "Dùng structured outputs (output_config.format) để ép định dạng."
        )

    if errors:
        raise ModelRuleError("Request sẽ lỗi 400:\n- " + "\n- ".join(errors))
