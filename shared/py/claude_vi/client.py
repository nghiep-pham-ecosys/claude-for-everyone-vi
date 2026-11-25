"""Điểm vào duy nhất mà notebook và bài tập dùng để gọi Claude."""
from __future__ import annotations

import json
import os
from typing import Any

from anthropic.types import Message, MessageTokensCount

from .config import REPO_ROOT, Settings
from .mock import BETA_THREADS, FIXTURE_DIR, MockAnthropic, request_key
from .rules import check_request


class MissingKeyError(RuntimeError):
    """Không ở mock mode mà cũng không có key: báo sớm, rõ ràng, thay vì TypeError của SDK lúc gọi."""


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
            from anthropic import Anthropic

            # Settings.from_env() đã nạp .env; kiểm lại ở đây vì Settings có thể được tạo tay
            from dotenv import load_dotenv

            load_dotenv(REPO_ROOT / ".env", override=False)
            if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")):
                raise MissingKeyError(
                    "Chưa có API key. Chạy không cần key: đặt CLAUDE_MOCK=1. "
                    "Chạy thật: cp .env.example .env rồi điền ANTHROPIC_API_KEY (xem modules/00-setup)."
                )
            self._client = Anthropic()

    @property
    def mock(self) -> MockAnthropic | None:
        """Client mock đang dùng (để giả lập hết hạn cache/thread trong bài học), None khi gọi API thật."""
        return self._client if isinstance(self._client, MockAnthropic) else None

    def _prepare(self, params: dict[str, Any]) -> dict[str, Any]:
        params.setdefault("model", self.settings.model)
        params.setdefault("max_tokens", self.settings.max_tokens)
        if params["max_tokens"] > self.settings.max_tokens * 8:
            raise ValueError(
                f"max_tokens={params['max_tokens']} vượt trần học tập "
                f"({self.settings.max_tokens * 8}). Đặt MAX_TOKENS nếu thật sự cần."
            )
        check_request(params)  # chặn lỗi 400 trước khi tốn tiền
        return params

    def create(self, **params: Any) -> Message:
        """thread={"type": "create"} hoặc {"type": "continue", "previous_message_id": ...}: message threads (beta).

        Request continue chỉ có message mới nên không kiểm luật ở đây được: tự giữ bản sao cả hội thoại và kiểm
        bằng check_request (module 06, mục 8). SDK 1.17.0 chưa có tham số thread, nên gửi qua extra_body.
        """
        thread = params.pop("thread", None)
        if thread is not None:
            if thread.get("type") == "continue":
                params.setdefault("model", self.settings.model)
                params.setdefault("max_tokens", self.settings.max_tokens)
            else:
                params = self._prepare(params)
            headers = dict(params.pop("extra_headers", None) or {})
            betas = [b for b in headers.get("anthropic-beta", "").split(",") if b.strip()]
            headers["anthropic-beta"] = ",".join([*betas, BETA_THREADS])
            body = {**(params.pop("extra_body", None) or {}), "thread": thread}
            return self._client.messages.create(**params, extra_body=body, extra_headers=headers)
        params = self._prepare(params)
        msg = self._client.messages.create(**params)
        if self.settings.record and not self.settings.mock:
            FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
            path = FIXTURE_DIR / f"{request_key(params)}.json"
            path.write_text(json.dumps(msg.model_dump(mode="json"), ensure_ascii=False, indent=2), "utf-8")
        return msg

    def stream(self, **params: Any) -> Any:
        """Như create() nhưng trả stream; dùng giống SDK:

        >>> with c.stream(messages=[...]) as s:
        ...     for chunk in s.text_stream:
        ...         print(chunk, end="", flush=True)
        ...     msg = s.get_final_message()

        Mock trả MockMessageStream (event đã validate bằng type SDK); thật trả
        MessageStreamManager của SDK. CLAUDE_RECORD chưa hỗ trợ stream.
        """
        return self._client.messages.stream(**self._prepare(params))

    def count_tokens(self, **params: Any) -> MessageTokensCount:
        """POST /v1/messages/count_tokens: miễn phí, không tạo message, không dùng cache. Không nhận max_tokens."""
        params.setdefault("model", self.settings.model)
        check_request(params)
        return self._client.messages.count_tokens(**params)

    def batch_create(self, requests: list[dict[str, Any]]) -> Any:
        """Message Batches: mỗi phần tử {"custom_id": ..., "params": {...}}. Kiểm luật từng request TRƯỚC khi gửi,
        vì API chỉ báo lỗi params khi cả batch đã xong (docs Batch processing)."""
        reqs = [{"custom_id": r["custom_id"], "params": self._prepare(dict(r["params"]))} for r in requests]
        return self._client.messages.batches.create(requests=reqs)

    def batch_retrieve(self, batch_id: str) -> Any:
        return self._client.messages.batches.retrieve(batch_id)

    def batch_results(self, batch_id: str) -> Any:
        """Iterator các MessageBatchIndividualResponse. Thứ tự KHÔNG theo request: ghép bằng custom_id."""
        return self._client.messages.batches.results(batch_id)

    def batch_cancel(self, batch_id: str) -> Any:
        return self._client.messages.batches.cancel(batch_id)

    def ask(self, prompt: str, system: str | None = None, **params: Any) -> Message:
        if system:
            params["system"] = system
        return self.create(messages=[{"role": "user", "content": prompt}], **params)


def text_of(msg: Message) -> str:
    """Ghép mọi block text, BỎ QUA block thinking/tool_use.

    Không dùng msg.content[0].text: trên model 5.x block đầu có thể là thinking.
    """
    return "".join(b.text for b in msg.content if b.type == "text")


def estimate_cost_usd(msg: Message, batch: bool = False) -> float:
    """Chi phí ước tính từ usage và giá trong config/models.yaml (module 06).

    Tính: input, output (gồm thinking), ghi cache 5 phút / 1 giờ, đọc cache, giá prompt dài (khi model có
    long_context, prompt tính cả token cache), batch=True nhân batch_price_multiplier. Chưa tính: inference_geo,
    fast mode, server tool. Model chưa có giá, hoặc có token cache mà chưa có giá cache: trả nan.
    """
    from .config import load_models

    cfg = load_models()
    entry = cfg["models"].get(msg.model, {})
    price, cache = entry.get("price_per_mtok"), entry.get("cache_price_per_mtok")
    if not price:
        return float("nan")
    u = msg.usage
    read, created = u.cache_read_input_tokens or 0, u.cache_creation_input_tokens or 0
    w1h = u.cache_creation.ephemeral_1h_input_tokens if u.cache_creation else 0
    long = entry.get("long_context")
    if long and u.input_tokens + read + created > long["over_tokens"]:
        price, cache = long["price_per_mtok"], long.get("cache_price_per_mtok", cache)
    if (read or created) and not cache:
        return float("nan")
    cost = u.input_tokens * price["input"] + u.output_tokens * price["output"]
    if cache:
        cost += (created - w1h) * cache["write_5m"] + w1h * cache["write_1h"] + read * cache["read"]
    return cost / 1_000_000 * (cfg.get("batch_price_multiplier", 1.0) if batch else 1.0)
