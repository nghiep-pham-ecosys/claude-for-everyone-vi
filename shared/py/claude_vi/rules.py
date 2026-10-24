"""Kiểm tra request theo luật của từng model, TRƯỚC khi gửi.

Mục đích: mock mode phải "đau" giống API thật. Nếu notebook dùng
temperature trên Haiku 5.5, CI phải đỏ chứ không được xanh giả.
"""
from __future__ import annotations

from typing import Any

from .config import load_models

SAMPLING_PARAMS = ("temperature", "top_p", "top_k")
EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")
# Từ khoá JSON Schema mà structured outputs / strict tool use không hỗ trợ (docs Structured outputs, kiểm 2026-10-24)
UNSUPPORTED_SCHEMA_KEYS = ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf",
                           "minLength", "maxLength")


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
    output_config = params.get("output_config") or {}
    effort = output_config.get("effort")
    if thinking.get("type") == "enabled" and "budget_tokens" in thinking:
        errors.append(
            "budget_tokens (extended thinking thủ công) đã bị bỏ trên model 5.x. "
            "Dùng adaptive thinking + output_config.effort."
        )
    elif thinking.get("type") == "enabled" and not rules.get("thinking_enabled_allowed", True):
        errors.append(f'thinking "enabled" không còn trên {model}. Bỏ trường thinking hoặc dùng "adaptive".')
    if thinking.get("type") == "disabled" and not rules.get("thinking_disabled_allowed", True):
        hint = ' Thử thinking={"type": "between_tools"}.' if rules.get("between_tools_allowed") else ""
        errors.append(f"Không tắt được thinking trên {model}.{hint}")
    if thinking.get("type") == "between_tools" and not rules.get("between_tools_allowed", False):
        errors.append(f'thinking "between_tools" chỉ có trên Sonnet 5.5, không có trên {model}.')
    if thinking.get("type") in ("disabled", "between_tools") and effort in ("xhigh", "max"):
        errors.append(f"effort '{effort}' cần thinking bật. Dùng effort 'high' trở xuống, hoặc bỏ trường thinking.")

    if effort is not None and effort not in EFFORT_LEVELS:
        hint = ' "adaptive" là chế độ thinking, không phải mức effort.' if effort == "adaptive" else ""
        errors.append(f"output_config.effort phải là một trong {', '.join(EFFORT_LEVELS)}.{hint}")
    fmt = output_config.get("format")
    if fmt is not None:
        if fmt.get("type") != "json_schema" or "schema" not in fmt:
            errors.append('output_config.format cần {"type": "json_schema", "schema": {...}}.')
        else:
            errors += [f"output_config.format: {e}" for e in schema_errors(fmt["schema"])]

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


def schema_errors(schema: Any, path: str = "schema") -> list[str]:
    """Các lỗi khiến structured outputs / strict tool use trả 400. Rỗng nghĩa là hợp lệ."""
    if not isinstance(schema, dict):
        return []
    errors = []
    if schema.get("type") == "object" or "properties" in schema:
        if schema.get("additionalProperties") is not False:
            errors.append(f"{path}: object phải có additionalProperties: false")
    for key in UNSUPPORTED_SCHEMA_KEYS:
        if key in schema:
            errors.append(f"{path}: không hỗ trợ '{key}' — kiểm giá trị trong code sau khi nhận kết quả")
    if schema.get("minItems", 0) > 1:
        errors.append(f"{path}: minItems chỉ được 0 hoặc 1")
    for name, sub in (schema.get("properties") or {}).items():
        errors += schema_errors(sub, f"{path}.{name}")
    if "items" in schema:
        errors += schema_errors(schema["items"], f"{path}[]")
    for key in ("anyOf", "allOf"):
        for i, sub in enumerate(schema.get(key) or []):
            errors += schema_errors(sub, f"{path}.{key}[{i}]")
    for key in ("$defs", "definitions"):
        for name, sub in (schema.get(key) or {}).items():
            errors += schema_errors(sub, f"{path}.{key}.{name}")
    return errors

