"""Kiểm tra request theo luật của từng model, TRƯỚC khi gửi.

Mục đích: mock mode phải "đau" giống API thật. Nếu notebook dùng
temperature trên Haiku 5.5, CI phải đỏ chứ không được xanh giả.
"""
from __future__ import annotations

import re
from typing import Any

from .config import load_models

SAMPLING_PARAMS = ("temperature", "top_p", "top_k")
EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")
# Từ khoá JSON Schema mà structured outputs / strict tool use không hỗ trợ (docs Structured outputs, kiểm 2026-10-24)
TOOL_NAME = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")  # docs Define tools, kiểm 2026-10-24
MAX_STRICT_TOOLS = 20
# Giới hạn độ phức tạp, tính GỘP trên mọi schema strict của một request (docs Structured outputs, kiểm 2026-11-09)
MAX_OPTIONAL_PARAMS = 24
MAX_UNION_PARAMS = 16
# Regex trong "pattern": không hỗ trợ backreference, lookahead/lookbehind, \b \B (docs Structured outputs)
UNSUPPORTED_REGEX = re.compile(r"\\[1-9]|\(\?<?[=!]|\\[bB]")
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

    errors += tool_errors(params)
    errors += complexity_errors(params)
    if fmt is not None and _citations_enabled(params):
        errors.append(
            "Citations và structured outputs không dùng chung được (docs Citations). "
            "Tách thành hai lời gọi (lượt trích dẫn rồi lượt JSON), hoặc xin mỗi trường một dòng "
            "\"ten: gia_tri\" có trích dẫn rồi tự tách trong code."
        )
    docs = [_field(b, "citations") for m in params.get("messages") or [] for b in _blocks(m)
            if _field(b, "type") == "document"]
    bat = [isinstance(c, dict) and bool(c.get("enabled")) for c in docs]
    if any(bat) and not all(bat):
        errors.append(
            f"Citations phải bật cho tất cả hoặc không document nào trong request "
            f"(đang bật {sum(bat)}/{len(bat)})."
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
    if isinstance(schema.get("pattern"), str) and UNSUPPORTED_REGEX.search(schema["pattern"]):
        errors.append(f"{path}: pattern dùng backreference, lookahead/lookbehind hoặc \\b — không được hỗ trợ")
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


def count_params(schema: Any) -> tuple[int, int]:
    """(số tham số optional, số tham số dùng union) trong một schema — cách docs tính giới hạn độ phức tạp.

    Optional: thuộc tính không nằm trong `required`. Union: thuộc tính dùng anyOf hoặc mảng type
    (ví dụ ["string", "null"]). $defs được đếm một lần dù được $ref nhiều chỗ.
    """
    if not isinstance(schema, dict):
        return 0, 0
    optional = union = 0
    props = schema.get("properties") or {}
    required = set(schema.get("required") or [])
    optional += sum(1 for name in props if name not in required)
    for sub in props.values():
        if isinstance(sub, dict) and ("anyOf" in sub or isinstance(sub.get("type"), list)):
            union += 1
    children = list(props.values())
    if isinstance(schema.get("items"), dict):
        children.append(schema["items"])
    for key in ("anyOf", "allOf"):
        children += schema.get(key) or []
    for key in ("$defs", "definitions"):
        children += list((schema.get(key) or {}).values())
    for sub in children:
        o, u = count_params(sub)
        optional, union = optional + o, union + u
    return optional, union


def complexity_errors(params: dict[str, Any]) -> list[str]:
    """Giới hạn gộp trên output_config.format và mọi tool strict trong cùng request."""
    schemas = []
    fmt = (params.get("output_config") or {}).get("format") or {}
    if isinstance(fmt.get("schema"), dict):
        schemas.append(fmt["schema"])
    schemas += [t["input_schema"] for t in params.get("tools") or [] if t.get("strict") and "input_schema" in t]
    if not schemas:
        return []
    optional = union = 0
    for s in schemas:
        o, u = count_params(s)
        optional, union = optional + o, union + u
    errors = []
    if optional > MAX_OPTIONAL_PARAMS:
        errors.append(f"Tổng {optional} tham số optional trên các schema strict (tối đa {MAX_OPTIONAL_PARAMS}). "
                      "Đưa bớt vào required, hoặc tách request.")
    if union > MAX_UNION_PARAMS:
        errors.append(f"Tổng {union} tham số dùng anyOf/mảng type trên các schema strict "
                      f"(tối đa {MAX_UNION_PARAMS}).")
    return errors


def _field(block: Any, name: str) -> Any:
    """Đọc trường của block dù là dict (tự viết) hay object SDK (msg.content gửi lại)."""
    return block.get(name) if isinstance(block, dict) else getattr(block, name, None)


def _blocks(message: dict[str, Any]) -> list[Any]:
    content = message.get("content")
    return content if isinstance(content, list) else []


def tool_errors(params: dict[str, Any]) -> list[str]:
    """Lỗi 400 liên quan tới tool: định nghĩa tool và cặp tool_use / tool_result."""
    errors = []
    tools = params.get("tools") or []
    for tool in tools:
        if "type" in tool and "input_schema" not in tool:
            continue  # tool có sẵn của Anthropic (web_search...), không phải tool tự định nghĩa
        name = tool.get("name", "")
        if not TOOL_NAME.match(name):
            errors.append(f"Tên tool '{name}' phải khớp ^[a-zA-Z0-9_-]{{1,128}}$ (không dấu, không khoảng trắng)")
        if "input_schema" not in tool:
            errors.append(f"Tool '{name}' thiếu input_schema")
        elif tool.get("strict"):
            errors += [f"tool '{name}' (strict): {e}" for e in schema_errors(tool["input_schema"], "input_schema")]
    if sum(1 for t in tools if t.get("strict")) > MAX_STRICT_TOOLS:
        errors.append(f"Tối đa {MAX_STRICT_TOOLS} tool strict trong một request")

    messages = params.get("messages") or []
    for i, msg in enumerate(messages):
        if msg.get("role") != "assistant":
            continue
        ids = [_field(b, "id") for b in _blocks(msg) if _field(b, "type") == "tool_use"]
        if not ids or i + 1 >= len(messages):
            continue
        nxt = messages[i + 1]
        blocks = _blocks(nxt)
        types = [_field(b, "type") for b in blocks]
        n_results = 0
        while n_results < len(types) and types[n_results] == "tool_result":
            n_results += 1
        answered = {_field(b, "tool_use_id") for b in blocks if _field(b, "type") == "tool_result"}
        if nxt.get("role") != "user" or set(ids) - answered:
            errors.append(
                f"messages.{i + 1}: tool_use ids were found without tool_result blocks immediately after: "
                f"{', '.join(sorted(set(ids) - answered))}. Mỗi tool_use cần một tool_result ngay lượt user kế tiếp."
            )
        elif "tool_result" in types[n_results:]:
            errors.append(f"messages.{i + 1}: các block tool_result phải đứng ĐẦU content, text đặt sau.")
        extra = answered - set(ids)
        if extra:
            errors.append(f"messages.{i + 1}: tool_result trỏ tới tool_use_id không có ở lượt trước: "
                          f"{', '.join(sorted(extra))}")
    return errors


def _citations_enabled(params: dict[str, Any]) -> bool:
    for msg in params.get("messages") or []:
        for block in _blocks(msg):
            citations = _field(block, "citations")
            if _field(block, "type") in ("document", "search_result") and isinstance(citations, dict) \
                    and citations.get("enabled"):
                return True
    return False

