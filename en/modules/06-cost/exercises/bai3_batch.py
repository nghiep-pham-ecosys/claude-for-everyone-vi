"""Exercise 3: build a batch by the rules, and group the results by custom_id.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
tao_requests = build the requests, viec = jobs, gom = group, ket_qua = results,
tra_loi = answers, loi = errors.

tao_requests(viec: dict[str, str]) -> list[dict]
    viec: key = a job code you choose, value = the question. Each job becomes one request
    {"custom_id": code, "params": {"messages": [{"role": "user", "content": question}]}}, in the dict's order.
    custom_id must match ^[a-zA-Z0-9_-]{1,64}$ (Batch processing docs). A bad code: raise ValueError (before
    sending). Check with re.fullmatch: with re.match, Python's `$` also matches before a newline at the end
    ("ok\n").
    An empty viec: raise ValueError.

gom(ket_qua) -> dict
    ket_qua: an iterable of MessageBatchIndividualResponse (in any order). Returns:
    {"tra_loi": {custom_id: text}         # only "succeeded" results, text taken with text_of
     "loi": {custom_id: type}             # "errored", "canceled", "expired"
     "usd": the sum of estimate_cost_usd(message, batch=True) over the succeeded requests}
    Only succeeded requests are billed.

Grade:  CHAM="$PWD/en/modules/06-cost/exercises" uv run pytest modules/06-cost -q
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from claude_vi import estimate_cost_usd, text_of  # noqa: F401


def tao_requests(viec: dict[str, str]) -> list[dict[str, Any]]:
    raise NotImplementedError("TODO: exercise 3")


def gom(ket_qua: Iterable[Any]) -> dict[str, Any]:
    raise NotImplementedError("TODO: exercise 3")
