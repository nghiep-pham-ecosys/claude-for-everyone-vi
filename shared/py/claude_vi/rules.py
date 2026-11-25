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
    errors += thinking_errors(thinking)

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
    errors += search_result_errors(params.get("messages") or [])
    docs = [_field(b, "citations") for m in params.get("messages") or [] for b in _blocks(m)
            if _field(b, "type") == "document"]
    bat = [isinstance(c, dict) and bool(c.get("enabled")) for c in docs]
    if any(bat) and not all(bat):
        errors.append(
            f"Citations phải bật cho tất cả hoặc không document nào trong request "
            f"(đang bật {sum(bat)}/{len(bat)})."
        )

    messages = params.get("messages") or []
    errors += system_message_errors(messages, model, rules)
    if messages and messages[-1].get("role") == "assistant" and not rules.get("assistant_prefill_allowed", True):
        errors.append(
            f"Prefill tin nhắn assistant không được hỗ trợ trên {model}. "
            "Dùng structured outputs (output_config.format) để ép định dạng."
        )

    errors += cache_control_errors(params)

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


THINKING_TYPES = ("adaptive", "enabled", "disabled", "between_tools")


def thinking_errors(thinking: dict[str, Any]) -> list[str]:
    """Hình dạng của trường thinking (docs Thinking, kiểm 2026-11-09). Luật theo model nằm ở check_request."""
    if not thinking:
        return []
    kind = thinking.get("type")
    if kind not in THINKING_TYPES:
        return [f"thinking.type phải là một trong {', '.join(THINKING_TYPES)}."]
    errors = []
    if kind == "between_tools" and set(thinking) - {"type"}:
        errors.append('thinking "between_tools" không nhận trường nào khác (display, budget_tokens, block_binding).')
    display = thinking.get("display")
    if display is not None:
        if kind in ("disabled", "between_tools"):
            if kind == "disabled":
                errors.append('display không dùng được với thinking "disabled": không có gì để hiển thị.')
        elif display == "updates":
            errors.append('display "updates" đang beta, cần header thinking-display-updates-2026-08-18; '
                          "claude_vi không gửi beta header. Dùng \"summarized\" hoặc \"omitted\".")
        elif display not in ("summarized", "omitted"):
            errors.append('thinking.display phải là "summarized" hoặc "omitted".')
    if "block_binding" in thinking:
        errors.append("thinking.block_binding cần beta header thinking-binding-controls-2026-08-01; "
                      "claude_vi không gửi beta header. Sửa code cho lịch sử append-only thay vì drop_block.")
    return errors


def system_message_errors(messages: list[dict[str, Any]], model: str, rules: dict[str, Any]) -> list[str]:
    """Message role "system" giữa hội thoại (docs Mid-conversation system messages, kiểm 2026-11-09)."""
    errors = []
    for i, m in enumerate(messages):
        if m.get("role") != "system":
            continue
        if not rules.get("mid_conversation_system_allowed", False):
            errors.append(f"messages.{i}: {model} không hỗ trợ message role system giữa hội thoại.")
            continue
        if "output_config" in m:
            errors.append(f"messages.{i}.output_config: effort theo từng message đang beta; claude_vi không gửi "
                          "beta header. Đổi effort ở lượt sau (mất cache), hoặc giữ nguyên.")
            continue
        if i == 0:
            errors.append(f"messages.{i}: message system có nội dung không được đứng đầu; dùng tham số system.")
        elif messages[i - 1].get("role") != "user":
            errors.append(f"messages.{i}: message system phải đứng ngay sau một lượt user "
                          "(kể cả lượt chỉ chứa tool_result).")
        if i + 1 < len(messages) and messages[i + 1].get("role") != "assistant":
            errors.append(f"messages.{i}: sau message system phải là lượt assistant, hoặc là cuối danh sách.")
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


MAX_CACHE_BREAKPOINTS = 4  # docs Prompt caching, FAQ (kiểm 2026-11-25)
CACHE_TTLS = ("5m", "1h")


def cache_breakpoints(params: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Mọi cache_control trong request, theo thứ tự prefix tools -> system -> messages, rồi tới cache_control
    cấp cao nhất (automatic caching, đặt lên block cuối của messages). Mỗi phần tử: (vị trí, cache_control)."""
    found = []
    for i, t in enumerate(params.get("tools") or []):
        if _field(t, "cache_control"):
            found.append((f"tools.{i}", _field(t, "cache_control")))
    system = params.get("system")
    for i, b in enumerate(system if isinstance(system, list) else []):
        if _field(b, "cache_control"):
            found.append((f"system.{i}", _field(b, "cache_control")))
    for i, m in enumerate(params.get("messages") or []):
        for j, b in enumerate(_blocks(m)):
            if _field(b, "cache_control"):
                found.append((f"messages.{i}.content.{j}", _field(b, "cache_control")))
    if params.get("cache_control"):
        found.append(("cache_control", params["cache_control"]))
    return found


def cache_control_errors(params: dict[str, Any]) -> list[str]:
    """cache_control sai hình dạng, quá 4 breakpoint, hoặc TTL 1 giờ đứng sau TTL 5 phút (docs Prompt caching,
    kiểm 2026-11-25). Automatic caching (cache_control cấp cao nhất) chiếm một trong 4 chỗ."""
    found = cache_breakpoints(params)
    errors = []
    for where, cc in found:
        if not isinstance(cc, dict) or cc.get("type") != "ephemeral":
            errors.append(f'{where}: cache_control phải là {{"type": "ephemeral"}} (kèm "ttl" nếu muốn).')
        elif cc.get("ttl", "5m") not in CACHE_TTLS:
            errors.append(f'{where}: cache_control.ttl phải là "5m" hoặc "1h".')
    if len(found) > MAX_CACHE_BREAKPOINTS:
        errors.append(f"Tối đa {MAX_CACHE_BREAKPOINTS} cache breakpoint mỗi request (đang có {len(found)}, "
                      "cache_control cấp cao nhất cũng tính là một).")
    top, msgs = params.get("cache_control"), params.get("messages") or []
    cuoi = _blocks(msgs[-1])[-1:] if msgs else []
    if isinstance(top, dict) and cuoi and isinstance(_field(cuoi[0], "cache_control"), dict) \
            and _field(cuoi[0], "cache_control").get("ttl", "5m") != top.get("ttl", "5m"):
        errors.append("cache_control cấp cao nhất có ttl khác với cache_control trên block cuối của messages.")
    ttls = [cc.get("ttl", "5m") for _, cc in found if isinstance(cc, dict)]
    if "5m" in ttls and "1h" in ttls[ttls.index("5m"):]:
        errors.append('Breakpoint ttl "1h" phải đứng trước mọi breakpoint ttl "5m" (theo thứ tự tools -> system '
                      "-> messages).")
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


def search_result_errors(messages: list[dict[str, Any]]) -> list[str]:
    """Block search_result (docs Search results, kiểm 2026-11-09)."""
    errors, found = [], []
    for i, m in enumerate(messages):
        for j, b in enumerate(_blocks(m)):
            kind = _field(b, "type")
            if kind == "search_result":
                if m.get("role") != "user":
                    errors.append(f"messages.{i}.content.{j}: search_result chỉ được đặt trong lượt user.")
                found.append((f"messages.{i}.content.{j}", b))
            elif kind == "tool_result" and isinstance(_field(b, "content"), list):
                inner = _field(b, "content")
                kinds = {_field(x, "type") for x in inner}
                if "search_result" in kinds and kinds != {"search_result"}:
                    errors.append(f"messages.{i}.content.{j}: tool_result có search_result thì mọi block bên "
                                  "trong phải là search_result; đặt text giải thích vào content của một search_result.")
                found += [(f"messages.{i}.content.{j}.content.{k}", x) for k, x in enumerate(inner)
                          if _field(x, "type") == "search_result"]
    for path, b in found:
        if not isinstance(_field(b, "source"), str) or not _field(b, "source"):
            errors.append(f"{path}: search_result cần source (URL hoặc mã ổn định, ví dụ kb://so-tay/3).")
        if not isinstance(_field(b, "title"), str):
            errors.append(f"{path}: search_result cần title.")
        content = _field(b, "content")
        if not isinstance(content, list) or not content:
            errors.append(f"{path}: search_result cần content là danh sách block text, không rỗng.")
        elif any(_field(x, "type") != "text" or not _field(x, "text") for x in content):
            errors.append(f"{path}: content của search_result chỉ gồm block text có chữ (không ảnh, không rỗng).")
    bat = [bool((_field(b, "citations") or {}).get("enabled")) for _, b in found]
    if any(bat) and not all(bat):
        errors.append(f"Citations của search_result phải bật cho tất cả hoặc không cái nào (đang bật {sum(bat)}/{len(bat)}).")
    return errors


def _citations_enabled(params: dict[str, Any]) -> bool:
    for msg in params.get("messages") or []:
        for block in _blocks(msg):
            citations = _field(block, "citations")
            if _field(block, "type") in ("document", "search_result") and isinstance(citations, dict) \
                    and citations.get("enabled"):
                return True
    return False

