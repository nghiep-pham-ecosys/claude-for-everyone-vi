"""Mock client: trả response đã ghi sẵn, ĐÃ VALIDATE bằng type thật của SDK.

Fixture được nạp qua anthropic.types.Message.model_validate, nên nếu
SDK đổi shape response, test sẽ hỏng ngay thay vì xanh giả. Streaming cũng
vậy: mỗi event giả lập đi qua RawMessageStreamEvent trước khi trả ra.
"""
from __future__ import annotations

import hashlib
import json
import re
import threading
import unicodedata
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Self

import anthropic
import httpx2
from anthropic.types import Message, MessageTokensCount, RawMessageStreamEvent
from anthropic.types.messages import MessageBatch, MessageBatchIndividualResponse
from pydantic import TypeAdapter

from .config import load_models
from .rules import _blocks, _field, check_request

FIXTURE_DIR = Path(__file__).parent / "fixtures"
_EVENT = TypeAdapter(RawMessageStreamEvent)

_DEFAULT_TEXT = "[MOCK] Xin chào! Đây là phản hồi giả lập."
_TEXT_TOKENS = 12
# Token thinking giả lập theo effort: đủ để thấy effort là "núm vặn" chi phí, không phải số thật
_THINKING_BY_EFFORT = {"low": 2, "medium": 6, "high": 12, "xhigh": 20, "max": 30}


# Mock đếm token theo quy ước 1 token ≈ 4 ký tự của dạng JSON từng block. KHÔNG phải tokenizer thật:
# đủ để thấy prompt dài thì tốn hơn và cache tính trên phần nào, không dùng để so với số thật.
_KY_TU_MOI_TOKEN = 4
BETA_THREADS = "message-threads-2026-08-12"  # docs Message threads (kiểm 2026-11-25)
_CUSTOM_ID = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")  # docs Batch processing (kiểm 2026-11-25)
_MAX_BATCH_REQUESTS = 100_000


def _bo_cache_control(x: Any) -> Any:
    x = _norm(x)
    return {k: v for k, v in x.items() if k != "cache_control"} if isinstance(x, dict) else x


def segments(params: dict[str, Any]) -> list[tuple[str, int, Any]]:
    """Prompt chia thành block theo thứ tự prefix của API: tools -> system -> messages.

    Mỗi phần tử: (text JSON của block, số token giả lập, cache_control của block hoặc None). cache_control
    không thuộc nội dung: đổi chỗ breakpoint không đổi prefix.
    """
    blocks: list[Any] = list(params.get("tools") or [])
    system = params.get("system")
    if isinstance(system, str):
        blocks.append({"type": "text", "text": system})
    elif system:
        blocks += list(system)
    for m in params.get("messages") or []:
        content = m.get("content")
        parts = [{"type": "text", "text": content}] if isinstance(content, str) else list(content or [])
        blocks += [{"role": m.get("role"), **_norm(b)} for b in parts]
    out = []
    for b in blocks:
        text = json.dumps(_bo_cache_control(b), sort_keys=True, ensure_ascii=False)
        out.append((text, -(-len(text) // _KY_TU_MOI_TOKEN), _field(b, "cache_control")))
    return out


def dem_token(params: dict[str, Any]) -> int:
    """Tổng token input giả lập của một request: cùng con số mà count_tokens của mock trả về."""
    return sum(n for _, n, _ in segments(params))


def request_key(params: dict[str, Any]) -> str:
    """Khoá ổn định cho một request (bỏ qua max_tokens để fixture dễ tái dùng)."""
    stable = {k: v for k, v in params.items() if k not in ("max_tokens", "stream")}
    raw = json.dumps(stable, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _khong_dau(text: str) -> str:
    """Chữ thường, bỏ dấu tiếng Việt, "_"/"-" thành khoảng trắng: "Quy trình" và "quy_trinh" về cùng một dạng."""
    text = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[_\-\s]+", " ", text).strip()


def _chon_enum(values: list[Any], hint: str | None) -> Any:
    """Giá trị enum đầu tiên (theo thứ tự trong schema) có xuất hiện nguyên từ trong `hint`; không có thì phần tử đầu.

    Mock không hiểu câu hỏi: nó chỉ dò từ khoá, để router có thể đi nhánh khác nhánh 1.
    """
    if hint:
        noi = f" {' '.join(_TU.findall(_khong_dau(hint)))} "
        for v in values:
            if isinstance(v, str) and (tu := _khong_dau(v)) and f" {tu} " in noi:
                return v
    return values[0]


def schema_instance(schema: Any, root: Any = None, hint: str | None = None) -> Any:
    """Một giá trị hợp lệ tối thiểu theo JSON schema — mock trả về khi có output_config.format.

    hint (lượt user cuối): `enum` chọn giá trị có từ khoá xuất hiện trong hint, không có thì phần tử đầu.
    """
    root = root if root is not None else schema
    if "$ref" in schema:
        name = schema["$ref"].split("/")[-1]
        defs = root.get("$defs") or root.get("definitions") or {}
        return schema_instance(defs[name], root, hint)
    if "const" in schema:
        return schema["const"]
    if "enum" in schema:
        return _chon_enum(schema["enum"], hint)
    for key in ("anyOf", "allOf"):
        if key in schema:
            return schema_instance(schema[key][0], root, hint)
    kind = schema.get("type")
    if isinstance(kind, list):
        kind = kind[0]
    if kind == "object" or "properties" in schema:
        props = schema.get("properties") or {}
        required = list(schema.get("required") or [])
        order = required + [k for k in props if k not in required]  # API: required trước, optional sau
        return {k: schema_instance(props[k], root, hint) for k in order}
    if kind == "array":
        return [schema_instance(schema.get("items") or {}, root, hint)]
    formats = {"date": "2026-01-01", "date-time": "2026-01-01T00:00:00Z", "email": "mock@example.com",
               "uri": "https://example.com", "uuid": "00000000-0000-0000-0000-000000000000"}
    return {"string": formats.get(schema.get("format"), "[MOCK]"), "integer": 0, "number": 0.0,
            "boolean": False, "null": None}.get(kind, "[MOCK]")


def _last_user_text(params: dict[str, Any]) -> str:
    """Chữ của lượt user gần nhất có chữ (bỏ qua lượt chỉ có tool_result)."""
    for m in reversed(params.get("messages") or []):
        if m.get("role") != "user":
            continue
        if isinstance(m.get("content"), str):
            return m["content"]
        texts = [_field(b, "text") or "" for b in _blocks(m) if _field(b, "type") == "text"]
        if texts:
            return " ".join(texts)
    return ""


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
    text = (json.dumps(schema_instance(fmt["schema"], hint=_last_user_text(params)), ensure_ascii=False)
            if fmt else _DEFAULT_TEXT)
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
            "input_tokens": dem_token(params),
            "output_tokens": out,
            "output_tokens_details": {"thinking_tokens": min(out, thinking)},
        },
    }


def _api_error(status: int, message: str | None = None, error_code: str | None = None) -> anthropic.APIStatusError:
    """Dựng đúng exception mà SDK ném khi API trả mã lỗi `status`. error_code -> error.details.error_code."""
    kinds = {
        400: (anthropic.BadRequestError, "invalid_request_error"),
        404: (anthropic.NotFoundError, "not_found_error"),
        429: (anthropic.RateLimitError, "rate_limit_error"),
        500: (anthropic.InternalServerError, "api_error"),
        529: (anthropic.OverloadedError, "overloaded_error"),
    }
    cls, err_type = kinds[status]
    body = {"type": "error", "error": {"type": err_type, "message": message or f"[MOCK] lỗi {status}"},
            "request_id": "req_mock"}
    if error_code:
        body["error"]["details"] = {"error_code": error_code}
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


_TU = re.compile(r"\w+(?:[-.,]\w+)*")


def _trung(cau_hoi: set[str], text: str) -> int:
    """Điểm trùng từ của mock: tổng độ dài các từ chung, nên mã như "e-22" nặng hơn "là"."""
    chung = cau_hoi & set(_TU.findall(text.lower()))
    return sum(len(w) * (3 if any(c.isdigit() for c in w) else 1) for w in chung if len(w) >= 2)


def search_results(params: dict[str, Any]) -> list[Any]:
    """Mọi block search_result trong request, đúng thứ tự API đánh search_result_index:
    theo thứ tự message, kể cả bên trong tool_result."""
    found = []
    for m in params.get("messages") or []:
        for b in _blocks(m):
            kind = _field(b, "type")
            if kind == "search_result":
                found.append(b)
            elif kind == "tool_result" and isinstance(_field(b, "content"), list):
                found += [x for x in _field(b, "content") if _field(x, "type") == "search_result"]
    return found


def _search_payload(params: dict[str, Any]) -> dict[str, Any] | None:
    """search_result có citations.enabled: trích khối khớp nhiều từ nhất với câu hỏi gần nhất.

    Mock không hiểu câu hỏi: nó chỉ đếm từ trùng, để học viên luyện ĐỌC search_result_location.
    """
    results = search_results(params)
    if not any((_field(r, "citations") or {}).get("enabled") for r in results):
        return None
    cau_hoi = _last_user_text(params)
    tu_hoi = set(_TU.findall(cau_hoi.lower()))
    chon = []
    for idx, r in enumerate(results):
        khoi = _field(r, "content") or []
        diem = [_trung(tu_hoi, _field(k, "text") or "") for k in khoi]
        if diem and max(diem) > 0:
            chon.append((max(diem), idx, diem.index(max(diem))))
    if not chon and results:
        chon = [(0, 0, 0)]
    blocks = []
    for _, idx, j in sorted(chon, key=lambda x: (-x[0], x[1]))[:3]:
        r = results[idx]
        text = _field(_field(r, "content")[j], "text")
        blocks.append({"type": "text", "text": text[:120] + "\n", "citations": [{
            "type": "search_result_location", "cited_text": text, "source": _field(r, "source"),
            "title": _field(r, "title"), "search_result_index": idx, "start_block_index": j,
            "end_block_index": j + 1}]})
    payload = _default_payload(params)
    thinking = [b for b in payload["content"] if b["type"] == "thinking"]
    payload["content"] = [*thinking, {"type": "text", "text": "[MOCK] Theo kết quả tìm kiếm:\n"}, *blocks]
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
            # cache_control không thuộc nội dung: đặt hay bỏ breakpoint không làm đổi prefix
            content = [_bo_cache_control(b) for b in content if _field(b, "type") not in _THINKING_TYPES]
        msgs.append({**m, "content": content})
    return _digest(params.get("system")), _digest(params.get("tools") or []), _digest(msgs)


class _MockMessages:
    def __init__(self, record_dir: Path | None = None, errors: list[int] | None = None,
                 redacted: bool = False, multi_step: bool = False) -> None:
        self._dir = record_dir or FIXTURE_DIR
        self._errors = list(errors or [])
        self._redacted = redacted
        self._multi_step = multi_step
        # Một khoá cho cả lời gọi: calls, bộ đếm id và bảng chữ ký thinking là trạng thái dùng chung giữa các luồng
        self._lock = threading.Lock()
        self._n = 0
        # tool_use id -> các block thinking/redacted của lượt đó: [("thinking", signature) | ("redacted_thinking", data)]
        self._issued: dict[str, list[tuple[str, str]]] = {}
        # signature hoặc data -> (text thinking đã trả, prefix lúc tạo block)
        self._thinking: dict[str, tuple[str, tuple[str, str, str]]] = {}
        # Prompt cache: khoá prefix -> ttl. Mock không có đồng hồ: cache không hết hạn trong một client
        # (gọi xoa_cache() để giả lập hết hạn).
        self._cache: dict[str, str] = {}
        # Message threads: id response -> {"params": hội thoại đầy đủ, "fixed": các trường cố định, "da_noi": bool}
        self._threads: dict[str, dict[str, Any]] = {}
        self.calls = 0
        self.count_calls = 0
        self.batches = _MockBatches(self)

    def xoa_cache(self) -> None:
        """Giả lập cache hết hạn (API thật: 5 phút hoặc 1 giờ không dùng tới)."""
        self._cache.clear()

    def het_han_threads(self) -> None:
        """Giả lập thread hết hạn (API thật: 5 phút sau request cuối): continue tiếp theo nhận 404."""
        self._threads.clear()

    def _cache_usage(self, params: dict[str, Any]) -> dict[str, Any]:
        """usage của phần input khi có prompt caching, theo docs Prompt caching (kiểm 2026-11-25):

        - Prefix theo thứ tự tools -> system -> messages; mỗi breakpoint dò ngược tối đa 20 block tìm prefix đã
          có trong cache (đọc). Chỉ GHI ở breakpoint, và chỉ khi prefix dài ít nhất cache_min_tokens của model.
        - input_tokens chỉ là phần SAU chỗ đọc/ghi cuối; tổng input = đọc + ghi + input_tokens.
        - Đổi model, thinking, effort (khác mặc định) hoặc tool_choice thì khoá khác: mất cache.
        - Trộn TTL: đọc trúng mục 5 phút nhưng một breakpoint 1 giờ phía sau trượt thì không tính là đọc.

        Khác API thật (đơn giản hoá): đổi effort/thinking làm mất cả prefix (API: chắc chắn mất phần messages,
        tuỳ model mất cả tools/system); thêm ảnh không làm mất cache; khi dò ngược, chuỗi tool_use/tool_result
        liền nhau vẫn đếm từng block (API đếm là một vị trí); cache không hết hạn theo thời gian.
        """
        segs = segments(params)
        total = sum(n for _, n, _ in segs)
        usage = {"input_tokens": total, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0,
                 "cache_creation": {"ephemeral_5m_input_tokens": 0, "ephemeral_1h_input_tokens": 0}}
        entry = load_models()["models"][params["model"]]
        minimum = entry.get("cache_min_tokens")
        bps = {i: cc for i, (_, _, cc) in enumerate(segs) if cc}
        if params.get("cache_control") and params.get("messages"):
            bps[len(segs) - 1] = params["cache_control"]  # automatic caching: block cuối của messages
        if not bps or minimum is None:
            return usage
        effort = (params.get("output_config") or {}).get("effort") or entry.get("default_effort")
        seed = [params["model"], _norm(params.get("thinking")), effort, _norm(params.get("tool_choice"))]
        h = hashlib.sha256(json.dumps(seed, sort_keys=True).encode())
        keys, cum, run = [], [], 0
        for text, n, _ in segs:
            h.update(text.encode())
            keys.append(h.hexdigest())
            run += n
            cum.append(run)
        read, read_ttl, hit = 0, None, -1
        for b in bps:
            for p in range(b, max(-1, b - 20), -1):
                if keys[p] in self._cache:
                    if cum[p] > read:
                        read, read_ttl, hit = cum[p], self._cache[keys[p]], p
                    break
        if read_ttl == "5m" and any(b > hit and bps[b].get("ttl") == "1h" and keys[b] not in self._cache
                                    for b in bps):
            read = 0  # docs "Mixing different TTLs": mục 5 phút không được tính khi breakpoint 1 giờ sau nó trượt
        prev = read
        for b in sorted(bps):
            if cum[b] < minimum:
                continue  # quá ngắn: không cache, không báo lỗi
            ttl = bps[b].get("ttl", "5m")
            if cum[b] > prev:
                usage["cache_creation"][f"ephemeral_{ttl}_input_tokens"] += cum[b] - prev
                prev = cum[b]
            self._cache[keys[b]] = ttl
        created = sum(usage["cache_creation"].values())
        usage.update(input_tokens=total - read - created, cache_creation_input_tokens=created,
                     cache_read_input_tokens=read)
        return usage

    def count_tokens(self, **params: Any) -> MessageTokensCount:
        """Như POST /v1/messages/count_tokens: không tạo message, không dùng cache, cùng luật 400 với create."""
        with self._lock:
            self.count_calls += 1
            if "thread" in (params.pop("extra_body", None) or {}):
                raise _api_error(400, "thread: token counting không hỗ trợ message threads. Đếm cả hội thoại.",
                                 "thread_unsupported_request")
            params.pop("extra_headers", None)
            if "max_tokens" in params:
                raise TypeError("count_tokens() không nhận max_tokens")  # giống SDK: không có tham số này
            check_request(params)
            return MessageTokensCount(input_tokens=dem_token(params))

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
        """Có tools: lượt đầu gọi tool, lượt nhận tool_result thì trả lời. None nếu không liên quan tool.

        multi_step: mỗi lượt gọi MỘT tool chưa có kết quả trong lịch sử, theo thứ tự trong `tools`;
        đủ kết quả thì trả lời bằng mọi tool_result trong lịch sử.
        """
        tools = [t for t in params.get("tools") or [] if "input_schema" in t]
        choice = params.get("tool_choice") or {}
        if not tools or choice.get("type") == "none":
            return None
        payload = _default_payload(params)
        thinking = [b for b in payload["content"] if b["type"] == "thinking"]
        results = [b for b in _blocks(params["messages"][-1]) if _field(b, "type") == "tool_result"]
        if self._multi_step:
            called, answered = {}, set()
            for m in params.get("messages") or []:
                for b in _blocks(m):
                    if _field(b, "type") == "tool_use":
                        called[_field(b, "id")] = _field(b, "name")
                    elif _field(b, "type") == "tool_result":
                        answered.add(_field(b, "tool_use_id"))
            done = {called[i] for i in answered if i in called}
            todo = [t for t in tools if t["name"] not in done]
            if todo and choice.get("type") not in ("any", "tool"):
                return self._call_tools(payload, thinking, todo[:1], forced=False)
            if not todo:  # đủ kết quả: trả lời bằng mọi tool_result trong lịch sử, kể cả khi lượt cuối là chữ
                results = [b for m in params["messages"] for b in _blocks(m) if _field(b, "type") == "tool_result"]
        if results and (searched := _search_payload(params)):
            return searched
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
        return self._call_tools(payload, thinking, tools, forced=choice.get("type") in ("any", "tool"))

    def _call_tools(self, payload: dict[str, Any], thinking: list[dict[str, Any]], tools: list[dict[str, Any]],
                    forced: bool) -> dict[str, Any]:
        """Lượt gọi tool: một block tool_use cho mỗi tool trong `tools`, input tối thiểu theo input_schema."""
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
        with self._lock:
            return self._respond_locked(params)

    def _respond_locked(self, params: dict[str, Any], cache_view: dict[str, Any] | None = None) -> Message:
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
            payload = (self._tool_payload(params) or _search_payload(params) or _citation_payload(params)
                       or _default_payload(params))
            self._finish_thinking(payload, params)
            payload["usage"].update(self._cache_usage(cache_view or params))
        payload.setdefault("model", params["model"])
        return Message.model_validate(payload)

    def create(self, **params: Any) -> Message:
        thread = (params.pop("extra_body", None) or {}).get("thread")
        headers = params.pop("extra_headers", None) or {}
        if thread is None:
            return self._respond(params)
        with self._lock:
            return self._respond_thread(params, thread, headers)

    def stream(self, **params: Any) -> MockMessageStream:
        if (params.pop("extra_body", None) or {}).get("thread"):
            raise NotImplementedError("Mock chưa hỗ trợ stream trong message thread")
        params.pop("extra_headers", None)
        return MockMessageStream(self._respond(params))

    # Trường phải giữ nguyên suốt một thread (docs Message threads, "What to send", kiểm 2026-11-25)
    _THREAD_FIXED = ("model", "tool_choice", "thinking", "mcp_servers", "context_management", "output_config",
                     "cache_control")

    def _respond_thread(self, params: dict[str, Any], thread: dict[str, Any], headers: dict[str, str]) -> Message:
        """Message threads (beta): create lưu hội thoại theo id response; continue chỉ gửi message mới.

        Mock dựng lại hội thoại đầy đủ rồi trả lời như request thường, nên usage.input_tokens tính trên cả
        hội thoại. Docs chỉ nói "Threads do not change pricing"; con số này là suy luận của repo.
        """
        if BETA_THREADS not in headers.get("anthropic-beta", ""):
            raise _api_error(400, f"thread: cần header anthropic-beta: {BETA_THREADS}")
        fixed = {k: _norm(params.get(k)) for k in self._THREAD_FIXED}
        kind = thread.get("type")
        if kind == "create":
            full = params
        elif kind == "continue":
            if not thread.get("previous_message_id"):
                raise _api_error(400, "thread.previous_message_id: bắt buộc khi type là continue.")
            prev = self._threads.get(thread.get("previous_message_id"))
            if prev is None:
                raise _api_error(404, "thread: không tiếp tục được thread này. Gửi lại cả hội thoại.",
                                 "thread_not_found")
            if prev["da_noi"]:
                raise _api_error(400, "thread: mỗi id response chỉ tiếp tục được một lần.",
                                 "thread_already_continued")
            if "system" in params or "tools" in params:
                raise _api_error(400, "thread: system và tools chỉ gửi ở request create.")
            khac = [k for k in self._THREAD_FIXED if fixed[k] != prev["fixed"][k]]
            if khac:
                raise _api_error(400, f"thread: trường cố định khác lúc create: {', '.join(khac)}",
                                 "thread_fingerprint_mismatch")
            moi = list(params.get("messages") or [])
            full = {**prev["params"], **params, "messages": prev["params"]["messages"] + moi}
            # Breakpoint trên message đã lưu vẫn dùng để đọc cache nhưng không tính vào giới hạn 4: luật kiểm
            # trên bản bỏ chúng đi, cache tính trên bản giữ nguyên.
            cu = [{**m, "content": [_bo_cache_control(b) for b in m["content"]]} if isinstance(m["content"], list)
                  else m for m in prev["params"]["messages"]]
            msg = self._respond_locked({**full, "messages": cu + moi}, cache_view=full)
            prev["da_noi"] = True  # chỉ khi request thành công: lỗi trước khi model chạy không đổi thread
        else:
            raise _api_error(400, 'thread.type phải là "create" hoặc "continue".')
        if kind == "create":
            msg = self._respond_locked(full)
        self._n += 1
        msg = msg.model_copy(update={"id": f"msg_mock_thread_{self._n:03d}"})
        luu = {k: v for k, v in full.items() if k not in ("max_tokens", "stop_sequences", "metadata")}
        luu["messages"] = [*full["messages"], {"role": "assistant", "content": [_norm(b) for b in msg.content]}]
        self._threads[msg.id] = {"params": luu, "fixed": fixed, "da_noi": False}
        return msg


class _MockBatches:
    """Giống client.messages.batches ở phần bài học dùng tới: create, retrieve, results, cancel.

    Xử lý theo thứ tự, ngay trong lời gọi retrieve thứ `xong_sau_lan`, nên cache luôn trúng (API thật:
    cache trong batch chỉ "best-effort"). Kết quả trả theo thứ tự NGƯỢC request: luôn ghép bằng custom_id.
    """

    xong_sau_lan = 2  # số lần retrieve trước khi batch "ended"

    def __init__(self, messages: _MockMessages) -> None:
        self._m = messages
        self._data: dict[str, dict[str, Any]] = {}
        # Khoá riêng: _process gọi _respond, hàm đó lấy khoá của _MockMessages
        self._lock = threading.Lock()

    def create(self, *, requests: list[dict[str, Any]], **_: Any) -> MessageBatch:
        with self._lock:
            return self._create(list(requests))

    def _create(self, requests: list[dict[str, Any]]) -> MessageBatch:
        if not 1 <= len(requests) <= _MAX_BATCH_REQUESTS:
            raise _api_error(400, f"requests: cần từ 1 tới {_MAX_BATCH_REQUESTS:,} request.")
        ids = [r.get("custom_id") for r in requests]
        sai = [i for i in ids if not isinstance(i, str) or not _CUSTOM_ID.fullmatch(i)]
        if sai:
            raise _api_error(400, f"custom_id phải khớp ^[a-zA-Z0-9_-]{{1,64}}$: {sai[:3]}")
        if len(set(ids)) != len(ids):
            raise _api_error(400, "custom_id phải khác nhau trong một batch.")
        batch_id = f"msgbatch_mock_{len(self._data) + 1:03d}"
        self._data[batch_id] = {"requests": json.loads(json.dumps(requests, default=_norm)), "lan": 0,
                                "huy": False, "ket_qua": None}
        return self._batch(batch_id)

    def _process(self, d: dict[str, Any]) -> None:
        out = []
        for r in d["requests"]:
            params = dict(r["params"])
            if d["huy"]:
                result = {"type": "canceled"}
            else:
                loi = ("stream" if params.get("stream") else "max_tokens: 0" if params.get("max_tokens") == 0
                       else "thread" if "thread" in params else None)
                try:
                    if loi:  # docs: các tham số này không dùng được trong batch
                        raise _api_error(400, f"{loi}: không hỗ trợ trong Message Batches.")
                    result = {"type": "succeeded", "message": self._m._respond(params).model_dump(mode="json")}
                except (anthropic.APIStatusError, ValueError) as e:
                    loi = (e.body["error"] if isinstance(e, anthropic.APIStatusError)
                           else {"type": "invalid_request_error", "message": str(e)})
                    result = {"type": "errored", "error": {"type": "error", "error": {
                        "type": loi["type"], "message": loi["message"]}}}
            out.append({"custom_id": r["custom_id"], "result": result})
        d["ket_qua"] = out

    def _batch(self, batch_id: str) -> MessageBatch:
        d = self._data[batch_id]
        xong = d["ket_qua"] is not None
        dem = {"processing": 0 if xong else len(d["requests"]), "succeeded": 0, "errored": 0, "canceled": 0,
               "expired": 0}
        for r in d["ket_qua"] or []:
            dem[r["result"]["type"]] += 1
        status = "ended" if xong else "canceling" if d["huy"] else "in_progress"
        return MessageBatch.model_validate({
            "id": batch_id, "type": "message_batch", "processing_status": status, "request_counts": dem,
            "created_at": "2026-01-01T00:00:00Z", "expires_at": "2026-01-02T00:00:00Z",
            "ended_at": "2026-01-01T00:10:00Z" if xong else None, "archived_at": None,
            "cancel_initiated_at": "2026-01-01T00:01:00Z" if d["huy"] else None,
            "results_url": f"https://api.anthropic.com/v1/messages/batches/{batch_id}/results" if xong else None,
        })

    def retrieve(self, message_batch_id: str, **_: Any) -> MessageBatch:
        with self._lock:
            d = self._data.get(message_batch_id)
            if d is None:
                raise _api_error(404, f"Không có batch {message_batch_id}")
            d["lan"] += 1
            if d["ket_qua"] is None and (d["huy"] or d["lan"] >= self.xong_sau_lan):
                self._process(d)
            return self._batch(message_batch_id)

    def cancel(self, message_batch_id: str, **_: Any) -> MessageBatch:
        with self._lock:
            d = self._data[message_batch_id]
            if d["ket_qua"] is None:
                d["huy"] = True
            return self._batch(message_batch_id)

    def results(self, message_batch_id: str, **_: Any) -> Iterator[MessageBatchIndividualResponse]:
        with self._lock:
            return self._results(message_batch_id)

    def _results(self, message_batch_id: str) -> Iterator[MessageBatchIndividualResponse]:
        d = self._data[message_batch_id]
        if d["ket_qua"] is None:
            # Giống SDK: results() đọc results_url, chưa "ended" thì chưa có
            raise anthropic.AnthropicError(f"No `results_url` for the given batch; Has it finished processing? "
                                           f"{self._batch(message_batch_id).processing_status}")
        return iter([MessageBatchIndividualResponse.model_validate(r) for r in reversed(d["ket_qua"])])


class MockAnthropic:
    """Thay thế tối thiểu cho anthropic.Anthropic trong CI.

    errors=[529, 429] -> hai lời gọi đầu ném OverloadedError rồi RateLimitError,
    giống SDK thật, để luyện xử lý lỗi mà không cần làm quá tải API.
    redacted=True     -> sau mỗi block thinking có thêm một block redacted_thinking, như khi API
                         che một phần suy nghĩ vì lý do an toàn (hiếm gặp, nhưng code phải chịu được).
    multi_step=True   -> agent nhiều bước: mỗi lượt gọi MỘT tool chưa có kết quả trong lịch sử (theo thứ tự
                         trong `tools`), đủ kết quả thì trả lời. Mặc định (False) gọi mọi tool ở lượt đầu.

    Nhiều luồng dùng chung một client được: mỗi lời gọi chạy trong một khoá (các lời gọi nối tiếp nhau).
    """

    def __init__(self, record_dir: Path | None = None, errors: list[int] | None = None,
                 redacted: bool = False, multi_step: bool = False) -> None:
        self.messages = _MockMessages(record_dir, errors, redacted, multi_step)
