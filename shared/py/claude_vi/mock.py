"""Mock client: trả response đã ghi sẵn, ĐÃ VALIDATE bằng type thật của SDK.

Fixture được nạp qua anthropic.types.Message.model_validate, nên nếu
SDK đổi shape response, test sẽ hỏng ngay thay vì xanh giả. Streaming cũng
vậy: mỗi event giả lập đi qua RawMessageStreamEvent trước khi trả ra.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Self

import anthropic
import httpx2
from anthropic.types import Message, RawMessageStreamEvent
from pydantic import TypeAdapter

from .rules import check_request

FIXTURE_DIR = Path(__file__).parent / "fixtures"
_EVENT = TypeAdapter(RawMessageStreamEvent)

_DEFAULT_TEXT = "[MOCK] Xin chào! Đây là phản hồi giả lập."
_DEFAULT_OUTPUT_TOKENS = 18
_DEFAULT_THINKING_TOKENS = 6


def request_key(params: dict[str, Any]) -> str:
    """Khoá ổn định cho một request (bỏ qua max_tokens để fixture dễ tái dùng)."""
    stable = {k: v for k, v in params.items() if k not in ("max_tokens", "stream")}
    raw = json.dumps(stable, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _default_payload(params: dict[str, Any]) -> dict[str, Any]:
    # Model 5.x có adaptive thinking bật mặc định: response có thể BẮT ĐẦU
    # bằng block thinking (text rỗng khi display="omitted"). Mock mô phỏng
    # đúng điều này để học viên không viết msg.content[0].text.
    text, out, stop = _DEFAULT_TEXT, _DEFAULT_OUTPUT_TOKENS, "end_turn"
    max_tokens = params.get("max_tokens", out)
    if max_tokens < out:
        # Giống API thật: thinking + text cùng tính vào max_tokens, hết trần thì cắt ngang
        keep = max(0, max_tokens - _DEFAULT_THINKING_TOKENS)
        text = text[: len(text) * keep // (out - _DEFAULT_THINKING_TOKENS)]
        out, stop = max_tokens, "max_tokens"
    return {
        "id": "msg_mock_default",
        "type": "message",
        "role": "assistant",
        "model": params["model"],
        "content": [
            {"type": "thinking", "thinking": "", "signature": "mock-signature"},
            {"type": "text", "text": text},
        ],
        "stop_reason": stop,
        "stop_sequence": None,
        "usage": {
            "input_tokens": 12,
            "output_tokens": out,
            "output_tokens_details": {"thinking_tokens": min(out, _DEFAULT_THINKING_TOKENS)},
        },
    }


def _api_error(status: int) -> anthropic.APIStatusError:
    """Dựng đúng exception mà SDK ném khi API trả mã lỗi `status`."""
    kinds = {
        400: (anthropic.BadRequestError, "invalid_request_error"),
        429: (anthropic.RateLimitError, "rate_limit_error"),
        500: (anthropic.InternalServerError, "api_error"),
        529: (anthropic.OverloadedError, "overloaded_error"),
    }
    cls, err_type = kinds[status]
    body = {"type": "error", "error": {"type": err_type, "message": f"[MOCK] lỗi {status}"},
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


class _MockMessages:
    def __init__(self, record_dir: Path | None = None, errors: list[int] | None = None) -> None:
        self._dir = record_dir or FIXTURE_DIR
        self._errors = list(errors or [])
        self.calls = 0

    def _respond(self, params: dict[str, Any]) -> Message:
        self.calls += 1
        if self._errors:
            raise _api_error(self._errors.pop(0))
        check_request(params)
        path = self._dir / f"{request_key(params)}.json"
        payload = json.loads(path.read_text("utf-8")) if path.exists() else _default_payload(params)
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
    """

    def __init__(self, record_dir: Path | None = None, errors: list[int] | None = None) -> None:
        self.messages = _MockMessages(record_dir, errors)
