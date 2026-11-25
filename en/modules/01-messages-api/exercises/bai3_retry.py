"""Exercise 3: retry with exponential backoff.

The real SDK already does this (max_retries=2). This exercise shows WHAT it does,
and you can use it when you call through a layer with no built-in retry.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
tinh_cho = compute the wait, lan = attempt, tran = cap, goi_co_retry = call with retry,
CO_THE_THU_LAI = can be retried.

tinh_cho(lan, retry_after=None, base=0.5, tran=8.0, rand=random.random) -> seconds to wait
    - A retry-after header that reads as a number -> return exactly that number.
    - Otherwise: wait = min(tran, base * 2**lan), then multiply by (0.5 + rand()/2)  ("equal jitter":
      wait from 50% to 100%, so many clients do not all retry at the same moment).

goi_co_retry(fn, max_retries=3, sleep=time.sleep, rand=random.random)
    - Call fn(). A temporary error (CO_THE_THU_LAI) -> sleep(tinh_cho(...)), then call again.
    - Read retry-after from e.response.headers if it is there.
    - At most max_retries RETRIES (so max_retries + 1 calls); after that, raise the last error again.
    - Any other error (400, ModelRuleError, ...) is raised right away, with no wait.

Grade:  CHAM="$PWD/en/modules/01-messages-api/exercises" uv run pytest modules/01-messages-api -q
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
    raise NotImplementedError("TODO: exercise 3")


def goi_co_retry(fn: Callable[[], T], max_retries: int = 3, sleep: Callable[[float], None] = time.sleep,
                 rand: Callable[[], float] = random.random) -> T:
    raise NotImplementedError("TODO: exercise 3")
