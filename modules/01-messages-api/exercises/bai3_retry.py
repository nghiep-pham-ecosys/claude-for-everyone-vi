"""Bài 3 — thử lại với exponential backoff.

SDK thật đã tự làm việc này (max_retries=2). Bài này để hiểu nó làm GÌ,
và để dùng khi gọi qua lớp không có retry sẵn.

tinh_cho(lan, retry_after=None, base=0.5, tran=8.0, rand=random.random) -> số giây chờ
    - Có header retry-after đọc được thành số -> trả đúng số đó.
    - Ngược lại: cho = min(tran, base * 2**lan), rồi nhân (0.5 + rand()/2)  ("equal jitter":
      chờ từ 50% tới 100%, để nhiều client không cùng thử lại một lúc).

goi_co_retry(fn, max_retries=3, sleep=time.sleep, rand=random.random)
    - Gọi fn(). Lỗi tạm thời (CO_THE_THU_LAI) -> sleep(tinh_cho(...)) rồi gọi lại.
    - Đọc retry-after từ e.response.headers nếu có.
    - Tối đa max_retries lần THỬ LẠI (tức max_retries + 1 lần gọi), hết thì ném lại lỗi cuối.
    - Lỗi khác (400, ModelRuleError, ...) ném ra ngay, không chờ.

Chấm:  CHAM=exercises uv run pytest modules/01-messages-api -q
"""
from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

import anthropic

T = TypeVar("T")

CO_THE_THU_LAI = (
    anthropic.RateLimitError,
    anthropic.OverloadedError,
    anthropic.InternalServerError,
    anthropic.APIConnectionError,
)


def tinh_cho(lan: int, retry_after: str | None = None, base: float = 0.5, tran: float = 8.0,
             rand: Callable[[], float] = random.random) -> float:
    raise NotImplementedError("TODO: bài 3")


def goi_co_retry(fn: Callable[[], T], max_retries: int = 3, sleep: Callable[[float], None] = time.sleep,
                 rand: Callable[[], float] = random.random) -> T:
    raise NotImplementedError("TODO: bài 3")
