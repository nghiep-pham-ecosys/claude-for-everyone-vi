"""Bài 3 — thử lại với exponential backoff. (LỜI GIẢI)"""
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
    if retry_after is not None:
        try:
            return float(retry_after)
        except ValueError:
            pass
    cho = min(tran, base * 2**lan)
    return cho * (0.5 + rand() / 2)


def goi_co_retry(fn: Callable[[], T], max_retries: int = 3, sleep: Callable[[float], None] = time.sleep,
                 rand: Callable[[], float] = random.random) -> T:
    for lan in range(max_retries + 1):
        try:
            return fn()
        except CO_THE_THU_LAI as e:
            if lan == max_retries:
                raise
            response = getattr(e, "response", None)
            retry_after = response.headers.get("retry-after") if response is not None else None
            sleep(tinh_cho(lan, retry_after, rand=rand))
    raise AssertionError("không tới được đây")
