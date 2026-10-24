"""Mock client: trả response đã ghi sẵn, ĐÃ VALIDATE bằng type thật của SDK.

Fixture được nạp qua anthropic.types.Message.model_validate, nên nếu
SDK đổi shape response, test sẽ hỏng ngay thay vì xanh giả.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from anthropic.types import Message

from .rules import check_request

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def request_key(params: dict[str, Any]) -> str:
    """Khoá ổn định cho một request (bỏ qua max_tokens để fixture dễ tái dùng)."""
    stable = {k: v for k, v in params.items() if k not in ("max_tokens", "stream")}
    raw = json.dumps(stable, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _default_payload(params: dict[str, Any]) -> dict[str, Any]:
    # Model 5.x có adaptive thinking bật mặc định: response có thể BẮT ĐẦU
    # bằng block thinking (text rỗng khi display="omitted"). Mock mô phỏng
    # đúng điều này để học viên không viết msg.content[0].text.
    return {
        "id": "msg_mock_default",
        "type": "message",
        "role": "assistant",
        "model": params["model"],
        "content": [
            {"type": "thinking", "thinking": "", "signature": "mock-signature"},
            {"type": "text", "text": "[MOCK] Xin chào! Đây là phản hồi giả lập."},
        ],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 12, "output_tokens": 18},
    }


class _MockMessages:
    def __init__(self, record_dir: Path | None = None) -> None:
        self._dir = record_dir or FIXTURE_DIR

    def create(self, **params: Any) -> Message:
        check_request(params)
        path = self._dir / f"{request_key(params)}.json"
        payload = json.loads(path.read_text("utf-8")) if path.exists() else _default_payload(params)
        payload.setdefault("model", params["model"])
        return Message.model_validate(payload)


class MockAnthropic:
    """Thay thế tối thiểu cho anthropic.Anthropic trong CI."""

    def __init__(self, record_dir: Path | None = None) -> None:
        self.messages = _MockMessages(record_dir)
