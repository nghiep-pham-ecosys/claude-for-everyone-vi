"""Mock client: trả response đã ghi sẵn, ĐÃ VALIDATE bằng type thật của SDK.

Fixture được nạp qua anthropic.types.Message.model_validate, nên nếu
SDK đổi shape response, test sẽ hỏng ngay thay vì xanh giả. Streaming cũng
vậy: mỗi event giả lập đi qua RawMessageStreamEvent trước khi trả ra.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Self

import anthropic
import httpx2
from anthropic.types import Message, RawMessageStreamEvent
from pydantic import TypeAdapter

from .config import load_models
from .rules import _blocks, _field, check_request

FIXTURE_DIR = Path(__file__).parent / "fixtures"
_EVENT = TypeAdapter(RawMessageStreamEvent)

_DEFAULT_TEXT = "[MOCK] Xin chào! Đây là phản hồi giả lập."
_TEXT_TOKENS = 12
# Token thinking giả lập theo effort: đủ để thấy effort là "núm vặn" chi phí, không phải số thật
_THINKING_BY_EFFORT = {"low": 2, "medium": 6, "high": 12, "xhigh": 20, "max": 30}


def request_key(params: dict[str, Any]) -> str:
    """Khoá ổn định cho một request (bỏ qua max_tokens để fixture dễ tái dùng)."""
    stable = {k: v for k, v in params.items() if k not in ("max_tokens", "stream")}
    raw = json.dumps(stable, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def schema_instance(schema: Any, root: Any = None) -> Any:
    """Một giá trị hợp lệ tối thiểu theo JSON schema — mock trả về khi có output_config.format."""
    root = root if root is not None else schema
    if "$ref" in schema:
        name = schema["$ref"].split("/")[-1]
        defs = root.get("$defs") or root.get("definitions") or {}
        return schema_instance(defs[name], root)
    if "const" in schema:
        return schema["const"]
    if "enum" in schema:
        return schema["enum"][0]
    for key in ("anyOf", "allOf"):
        if key in schema:
            return schema_instance(schema[key][0], root)
    kind = schema.get("type")
    if isinstance(kind, list):
        kind = kind[0]
    if kind == "object" or "properties" in schema:
        props = schema.get("properties") or {}
        required = list(schema.get("required") or [])
        order = required + [k for k in props if k not in required]  # API: required trước, optional sau
        return {k: schema_instance(props[k], root) for k in order}
    if kind == "array":
        return [schema_instance(schema.get("items") or {}, root)]
    formats = {"date": "2026-01-01", "date-time": "2026-01-01T00:00:00Z", "email": "mock@example.com",
               "uri": "https://example.com", "uuid": "00000000-0000-0000-0000-000000000000"}
    return {"string": formats.get(schema.get("format"), "[MOCK]"), "integer": 0, "number": 0.0,
            "boolean": False, "null": None}.get(kind, "[MOCK]")


def _default_payload(params: dict[str, Any]) -> dict[str, Any]:
    # Model 5.x có adaptive thinking bật mặc định: response có thể BẮT ĐẦU
    # bằng block thinking (text rỗng khi display="omitted"). Mock mô phỏng
    # đúng điều này để học viên không viết msg.content[0].text.
    from .config import load_models

    output_config = params.get("output_config") or {}
    effort = output_config.get("effort") or load_models()["models"][params["model"]].get("default_effort", "high")
    thinking_on = (params.get("thinking") or {}).get("type") not in ("disabled", "between_tools")
    thinking = _THINKING_BY_EFFORT[effort] if thinking_on else 0

    fmt = output_config.get("format")
    text = json.dumps(schema_instance(fmt["schema"]), ensure_ascii=False) if fmt else _DEFAULT_TEXT
    out, stop = thinking + _TEXT_TOKENS, "end_turn"
    max_tokens = params.get("max_tokens", out)
    if max_tokens < out:
        # Giống API thật: thinking + text cùng tính vào max_tokens, hết trần thì cắt ngang
        keep = max(0, max_tokens - thinking)
        text = text[: len(text) * keep // _TEXT_TOKENS]
        out, stop = max_tokens, "max_tokens"
    content = [{"type": "thinking", "thinking": "", "signature": "mock-signature"}] if thinking_on else []
    return {
        "id": "msg_mock_default",
        "type": "message",
        "role": "assistant",
        "model": params["model"],
        "content": [*content, {"type": "text", "text": text}],
        "stop_reason": stop,
        "stop_sequence": None,
        "usage": {
            "input_tokens": 12,
            "output_tokens": out,
            "output_tokens_details": {"thinking_tokens": min(out, thinking)},
        },
    }


def _api_error(status: int, message: str | None = None) -> anthropic.APIStatusError:
    """Dựng đúng exception mà SDK ném khi API trả mã lỗi `status`."""
    kinds = {
        400: (anthropic.BadRequestError, "invalid_request_error"),
        429: (anthropic.RateLimitError, "rate_limit_error"),
        500: (anthropic.InternalServerError, "api_error"),
        529: (anthropic.OverloadedError, "overloaded_error"),
    }
    cls, err_type = kinds[status]
    body = {"type": "error", "error": {"type": err_type, "message": message or f"[MOCK] lỗi {status}"},
            "request_id": "req_mock"}
    headers = {"request-id": "req_mock"}
    if status == 429:
        headers["retry-after"] = "1"
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx2.Response(status, json=body, headers=headers, request=request)
    return cls(f"Error code: {status} - {body}", response=response, body=body)


def _events(msg: Message) -> Iterator[dict[str, Any]]:
    """Tách một Message hoàn chỉnh thành chuỗi event SSE theo đúng thứ tự của API."""
    start = msg.model_dump(mode="json")
    start.update(content=[], stop_reason=None, stop_sequence=None)
    start["usage"] = {"input_tokens": msg.usage.input_tokens, "output_tokens": 1}
    yield {"type": "message_start", "message": start}
    # API còn gửi event "ping"; SDK lọc bỏ trước khi trả ra nên mock cũng không có
    for i, block in enumerate(msg.content):
        if block.type == "thinking":
            yield {"type": "content_block_start", "index": i,
                   "content_block": {"type": "thinking", "thinking": "", "signature": ""}}
            yield {"type": "content_block_delta", "index": i,
                   "delta": {"type": "thinking_delta", "thinking": block.thinking}}
            yield {"type": "content_block_delta", "index": i,
                   "delta": {"type": "signature_delta", "signature": block.signature}}
        elif block.type == "text":
            yield {"type": "content_block_start", "index": i, "content_block": {"type": "text", "text": ""}}
            for j in range(0, len(block.text), 8):
                yield {"type": "content_block_delta", "index": i,
                       "delta": {"type": "text_delta", "text": block.text[j : j + 8]}}
            # docs Citations: mỗi citations_delta mang MỘT trích dẫn để nối vào block text hiện tại
            for cit in block.citations or []:
                yield {"type": "content_block_delta", "index": i,
                       "delta": {"type": "citations_delta", "citation": cit.model_dump(mode="json")}}
        elif block.type == "redacted_thinking":
            # không có delta: block đến nguyên vẹn trong content_block_start
            yield {"type": "content_block_start", "index": i,
                   "content_block": {"type": "redacted_thinking", "data": block.data}}
        elif block.type == "tool_use":
            yield {"type": "content_block_start", "index": i,
                   "content_block": {"type": "tool_use", "id": block.id, "name": block.name, "input": {}}}
            yield {"type": "content_block_delta", "index": i,
                   "delta": {"type": "input_json_delta", "partial_json": json.dumps(block.input, ensure_ascii=False)}}
        else:
            raise NotImplementedError(f"Mock chưa stream được block '{block.type}'")
        yield {"type": "content_block_stop", "index": i}
    usage = msg.usage.model_dump(mode="json", exclude_none=True, include={"output_tokens", "output_tokens_details"})
    yield {"type": "message_delta", "delta": {"stop_reason": msg.stop_reason, "stop_sequence": msg.stop_sequence},
           "usage": usage}
    yield {"type": "message_stop"}


class MockMessageStream:
    """Giống `anthropic.lib.streaming.MessageStream` ở phần bài học dùng tới.

    >>> with client.stream(messages=[...]) as s:
    ...     for chunk in s.text_stream: print(chunk, end="")
    ...     msg = s.get_final_message()
    """

    def __init__(self, msg: Message) -> None:
        self._final = msg
        self._iter = (_EVENT.validate_python(e) for e in _events(msg))

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def __iter__(self) -> Iterator[RawMessageStreamEvent]:
        return self._iter

    @property
    def text_stream(self) -> Iterator[str]:
        for event in self:
            if event.type == "content_block_delta" and event.delta.type == "text_delta":
                yield event.delta.text

    def until_done(self) -> None:
        for _ in self:
            pass

    def get_final_message(self) -> Message:
        self.until_done()
        return self._final


_SO = re.compile(r"\d+(?:[.,]\d+)?")


def _cau_co_so_lieu(text: str) -> bool:
    """Heuristic của mock: một câu "có số liệu" nếu kết thúc bằng dấu chấm và có ít nhất 2 con số."""
    return text.strip().endswith(".") and len(_SO.findall(text)) >= 2


def _citation_payload(params: dict[str, Any]) -> dict[str, Any] | None:
    """Document có citations.enabled: trích mọi câu có số liệu, kèm vị trí như API thật.

    Mock không hiểu nội dung — nó chỉ chọn câu theo heuristic để học viên luyện ĐỌC citations.
    """
    docs = [b for m in params.get("messages") or [] for b in _blocks(m) if _field(b, "type") == "document"]
    if not any((_field(d, "citations") or {}).get("enabled") for d in docs):
        return None
    blocks = []
    for idx, doc in enumerate(docs):
        if not (_field(doc, "citations") or {}).get("enabled"):
            continue
        source = _field(doc, "source") or {}
        title = _field(doc, "title")
        if source.get("media_type") == "application/pdf":
            import base64
            import io

            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(base64.b64decode(source["data"])))
            for page_no, page in enumerate(reader.pages, 1):
                for line in (page.extract_text() or "").splitlines():
                    if _cau_co_so_lieu(line):
                        blocks.append({"type": "text", "text": line.strip(), "citations": [{
                            "type": "page_location", "cited_text": line.strip(), "document_index": idx,
                            "document_title": title, "start_page_number": page_no,
                            "end_page_number": page_no + 1}]})
        elif source.get("type") == "content":
            # Custom content: API không cắt nhỏ thêm, mỗi block là một đơn vị trích dẫn (chỉ số từ 0, end không tính)
            for j, chunk in enumerate(source.get("content") or []):
                text = _field(chunk, "text") or ""
                if len(_SO.findall(text)) >= 2:
                    blocks.append({"type": "text", "text": text.strip(), "citations": [{
                        "type": "content_block_location", "cited_text": text, "document_index": idx,
                        "document_title": title, "start_block_index": j, "end_block_index": j + 1}]})
        elif source.get("type") == "text":
            data = source["data"]
            # câu kết thúc ở dấu chấm theo sau là khoảng trắng hoặc hết chuỗi (không cắt ở "7.1")
            for m in re.finditer(r"\S[^\n]*?\.(?=\s|$)", data):
                if _cau_co_so_lieu(m.group()):
                    blocks.append({"type": "text", "text": m.group(), "citations": [{
                        "type": "char_location", "cited_text": m.group(), "document_index": idx,
                        "document_title": title, "start_char_index": m.start(), "end_char_index": m.end()}]})
    payload = _default_payload(params)
    thinking = [b for b in payload["content"] if b["type"] == "thinking"]
    intro = {"type": "text", "text": "[MOCK] Các câu có số liệu trong tài liệu:\n"}
    payload["content"] = [*thinking, intro, *blocks]
    return payload


_THINKING_MODIFIED = (
    "messages.{i}.content: `thinking` or `redacted_thinking` blocks in the latest assistant message cannot be "
    "modified. These blocks must remain as they were in the original response."
)
# docs Preserved thinking, mục "The 400 error" (kiểm 2026-11-09); câu cuối nói phần nào đã đổi
_PREFIX_MISMATCH = (
    "messages.{i}.content.{j}: Invalid `signature` in `thinking` block. The block is bound to a different "
    "conversation. Remove the block, or set `thinking.block_binding.prefix_mismatch_behavior` to \"drop_block\". "
    "That setting requires the `thinking-binding-controls-2026-08-01` value in the `anthropic-beta` header. "
    "{what} differs from when the block was created."
)
_THINKING_TYPES = ("thinking", "redacted_thinking")
_SUMMARY = "[MOCK] Tóm tắt suy nghĩ: đọc câu hỏi, thử một hướng, kiểm lại kết quả."


def _norm(x: Any) -> Any:
    """Dạng JSON ổn định của system/tools/messages, dù block là dict hay object SDK."""
    if hasattr(x, "model_dump"):
        x = x.model_dump(mode="json", exclude_none=True)
    if isinstance(x, dict):
        return {k: _norm(v) for k, v in x.items() if v is not None}
    if isinstance(x, (list, tuple)):
        return [_norm(v) for v in x]
    return x


def _digest(x: Any) -> str:
    return hashlib.sha256(json.dumps(_norm(x), sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def _prefix(params: dict[str, Any], upto: int) -> tuple[str, str, str]:
    """(system, tools, messages[:upto]) — phần docs gọi là prefix của một block thinking.

    Block thinking ở các lượt trước KHÔNG thuộc prefix (docs: bỏ block cũ nhất được phép),
    nên bị loại trước khi băm.
    """
    msgs = []
    for m in (params.get("messages") or [])[:upto]:
        content = m.get("content")
        if isinstance(content, list):
            content = [b for b in content if _field(b, "type") not in _THINKING_TYPES]
        msgs.append({**m, "content": content})
    return _digest(params.get("system")), _digest(params.get("tools") or []), _digest(msgs)


class _MockMessages:
    def __init__(self, record_dir: Path | None = None, errors: list[int] | None = None,
                 redacted: bool = False) -> None:
        self._dir = record_dir or FIXTURE_DIR
        self._errors = list(errors or [])
        self._redacted = redacted
        self._n = 0
        # tool_use id -> các block thinking/redacted của lượt đó: [("thinking", signature) | ("redacted_thinking", data)]
        self._issued: dict[str, list[tuple[str, str]]] = {}
        # signature hoặc data -> (text thinking đã trả, prefix lúc tạo block)
        self._thinking: dict[str, tuple[str, tuple[str, str, str]]] = {}
        self.calls = 0

    def _check_thinking_kept(self, params: dict[str, Any]) -> None:
        """Như API: lượt assistant cuối có tool_use phải giữ nguyên các block thinking/redacted của nó."""
        messages = params.get("messages") or []
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("role") == "assistant":
                break
        else:
            return
        blocks = _blocks(messages[i])
        ids = [_field(b, "id") for b in blocks if _field(b, "type") == "tool_use" and _field(b, "id") in self._issued]
        for kind, key in self._issued[ids[0]] if ids else []:
            if kind == "redacted_thinking":
                kept = any(_field(b, "type") == kind and _field(b, "data") == key for b in blocks)
            else:
                text = self._thinking[key][0]
                # docs: text đặt vào trường thinking rỗng (display omitted) bị bỏ qua, không bị từ chối
                kept = any(_field(b, "type") == kind and _field(b, "signature") == key
                           and (text == "" or _field(b, "thinking") == text) for b in blocks)
            if not kept:
                raise _api_error(400, _THINKING_MODIFIED.format(i=i))

    def _check_prefix(self, params: dict[str, Any]) -> None:
        """Prefix check: block thinking chỉ hợp lệ khi system, tools và các message trước nó không đổi.

        Mock giả định tài khoản tạo từ 31/8/2026 trở đi: lệch prefix là 400 trên mọi model có prefix check.
        """
        rules = load_models()["models"][params["model"]].get("rules", {})
        if not rules.get("prefix_check"):
            return
        for i, m in enumerate(params.get("messages") or []):
            if m.get("role") != "assistant":
                continue
            for j, b in enumerate(_blocks(m)):
                kind = _field(b, "type")
                key = _field(b, "signature" if kind == "thinking" else "data") if kind in _THINKING_TYPES else None
                if key not in self._thinking:
                    continue  # block không do mock này tạo (test tự dựng, fixture) -> không kiểm được
                then, now = self._thinking[key][1], _prefix(params, i)
                if then != now:
                    what = ("The `system` prompt" if then[0] != now[0] else
                            "The `tools` list" if then[1] != now[1] else "An earlier message")
                    raise _api_error(400, _PREFIX_MISMATCH.format(i=i, j=j, what=what))

    def _finish_thinking(self, payload: dict[str, Any], params: dict[str, Any]) -> None:
        """Chữ ký riêng cho từng block, text tóm tắt khi display="summarized", tuỳ chọn thêm redacted_thinking."""
        display = (params.get("thinking") or {}).get("display", "omitted")
        prefix = _prefix(params, len(params.get("messages") or []))
        content, made = [], []
        for b in payload["content"]:
            if b["type"] != "thinking":
                content.append(b)
                continue
            self._n += 1
            text = _SUMMARY if display == "summarized" else ""
            b = {**b, "signature": b["signature"] if b["signature"].startswith("mock-sig-") else f"mock-sig-{self._n}",
                 "thinking": text}
            self._thinking[b["signature"]] = (text, prefix)
            content.append(b)
            made.append(("thinking", b["signature"]))
            if self._redacted:
                data = f"mock-redacted-{self._n}"
                self._thinking[data] = ("", prefix)
                content.append({"type": "redacted_thinking", "data": data})
                made.append(("redacted_thinking", data))
        payload["content"] = content
        for b in content:
            if b["type"] == "tool_use":
                self._issued[b["id"]] = made

    def _tool_payload(self, params: dict[str, Any]) -> dict[str, Any] | None:
        """Có tools: lượt đầu gọi tool, lượt nhận tool_result thì trả lời. None nếu không liên quan tool."""
        tools = [t for t in params.get("tools") or [] if "input_schema" in t]
        choice = params.get("tool_choice") or {}
        if not tools or choice.get("type") == "none":
            return None
        payload = _default_payload(params)
        thinking = [b for b in payload["content"] if b["type"] == "thinking"]
        results = [b for b in _blocks(params["messages"][-1]) if _field(b, "type") == "tool_result"]
        if results:
            parts = []
            for r in results:
                c = _field(r, "content")
                text = c if isinstance(c, str) else " ".join(_field(x, "text") or "" for x in (c or []))
                parts.append(("LỖI " if _field(r, "is_error") else "") + text[:60])
            payload["content"] = [*thinking, {"type": "text", "text": "[MOCK] Đã nhận kết quả tool: " + " | ".join(parts)}]
            return payload

        if choice.get("type") == "tool":
            tools = [t for t in tools if t["name"] == choice.get("name")]
        if choice.get("disable_parallel_tool_use") or choice.get("type") == "tool":
            tools = tools[:1]
        forced = choice.get("type") in ("any", "tool")
        calls = []
        for t in tools:
            self._n += 1
            tool_id = f"toolu_mock_{self._n:03d}"
            calls.append({"type": "tool_use", "id": tool_id, "name": t["name"], "input": schema_instance(t["input_schema"])})
        if forced:
            # docs: tool_choice any/tool bỏ qua thinking, response bắt đầu bằng tool_use
            payload["content"] = calls
            payload["usage"]["output_tokens_details"] = {"thinking_tokens": 0}
        else:
            payload["content"] = [*thinking, {"type": "text", "text": "[MOCK] Mình sẽ gọi tool."}, *calls]
        payload["stop_reason"] = "tool_use"
        return payload

    def _respond(self, params: dict[str, Any]) -> Message:
        self.calls += 1
        if self._errors:
            raise _api_error(self._errors.pop(0))
        check_request(params)
        self._check_thinking_kept(params)
        self._check_prefix(params)
        path = self._dir / f"{request_key(params)}.json"
        if path.exists():
            payload = json.loads(path.read_text("utf-8"))
        else:
            payload = self._tool_payload(params) or _citation_payload(params) or _default_payload(params)
            self._finish_thinking(payload, params)
        payload.setdefault("model", params["model"])
        return Message.model_validate(payload)

    def create(self, **params: Any) -> Message:
        return self._respond(params)

    def stream(self, **params: Any) -> MockMessageStream:
        return MockMessageStream(self._respond(params))


class MockAnthropic:
    """Thay thế tối thiểu cho anthropic.Anthropic trong CI.

    errors=[529, 429] -> hai lời gọi đầu ném OverloadedError rồi RateLimitError,
    giống SDK thật, để luyện xử lý lỗi mà không cần làm quá tải API.
    redacted=True     -> sau mỗi block thinking có thêm một block redacted_thinking, như khi API
                         che một phần suy nghĩ vì lý do an toàn (hiếm gặp, nhưng code phải chịu được).
    """

    def __init__(self, record_dir: Path | None = None, errors: list[int] | None = None,
                 redacted: bool = False) -> None:
        self.messages = _MockMessages(record_dir, errors, redacted)
