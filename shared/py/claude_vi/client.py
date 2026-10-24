"""Điểm vào duy nhất mà notebook và bài tập dùng để gọi Claude."""
from __future__ import annotations

import json
from typing import Any

from anthropic.types import Message

from .config import Settings
from .mock import FIXTURE_DIR, MockAnthropic, request_key
from .rules import check_request


class ClaudeVi:
    """
    >>> c = ClaudeVi()                      # đọc .env / biến môi trường
    >>> msg = c.ask("Giải thích prompt caching trong 2 câu")
    >>> print(text_of(msg))

    CLAUDE_MOCK=1   -> không gọi mạng, dùng fixture
    CLAUDE_RECORD=1 -> gọi API thật và lưu response làm fixture
    """

    def __init__(self, settings: Settings | None = None, client: Any = None) -> None:
        self.settings = settings or Settings.from_env()
        if client is not None:
            self._client = client
        elif self.settings.mock:
            self._client = MockAnthropic()
        else:
            from dotenv import load_dotenv
            from anthropic import Anthropic

            load_dotenv()
            self._client = Anthropic()

    def create(self, **params: Any) -> Message:
        params.setdefault("model", self.settings.model)
        params.setdefault("max_tokens", self.settings.max_tokens)
        if params["max_tokens"] > self.settings.max_tokens * 8:
            raise ValueError(
                f"max_tokens={params['max_tokens']} vượt trần học tập "
                f"({self.settings.max_tokens * 8}). Đặt MAX_TOKENS nếu thật sự cần."
            )
        check_request(params)  # chặn lỗi 400 trước khi tốn tiền
        msg = self._client.messages.create(**params)
        if self.settings.record and not self.settings.mock:
            path = FIXTURE_DIR / f"{request_key(params)}.json"
            path.write_text(json.dumps(msg.model_dump(mode="json"), ensure_ascii=False, indent=2), "utf-8")
        return msg

    def ask(self, prompt: str, system: str | None = None, **params: Any) -> Message:
        if system:
            params["system"] = system
        return self.create(messages=[{"role": "user", "content": prompt}], **params)


def text_of(msg: Message) -> str:
    """Ghép mọi block text, BỎ QUA block thinking/tool_use.

    Không dùng msg.content[0].text: trên model 5.x block đầu có thể là thinking.
    """
    return "".join(b.text for b in msg.content if b.type == "text")


def estimate_cost_usd(msg: Message) -> float:
    from .config import load_models

    price = load_models()["models"].get(msg.model, {}).get("price_per_mtok")
    if not price:
        return float("nan")
    u = msg.usage
    return (u.input_tokens * price["input"] + u.output_tokens * price["output"]) / 1_000_000
