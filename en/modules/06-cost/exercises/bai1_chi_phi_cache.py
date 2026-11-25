"""Exercise 1: the full cost of a response with prompt caching and batch.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
chi_phi = cost, so_lan_doc_hoa_von = number of reads to break even, ghi = write, doc = read, tong = total.

Prices are read from config/models.yaml through load_models()["models"][model]:
    price_per_mtok        {"input", "output"}
    cache_price_per_mtok  {"write_5m", "write_1h", "read"}
and load_models()["batch_price_multiplier"]. Do NOT type any price into the code.

chi_phi(msg, batch=False) -> dict of USD with the keys:
    "input"   usage.input_tokens x the input price
    "ghi_5m"  5-minute cache write tokens x write_5m
    "ghi_1h"  1-hour cache write tokens x write_1h
    "doc"     usage.cache_read_input_tokens x read
    "output"  usage.output_tokens x the output price
    "tong"    the sum of the 5 parts above
    batch=True: EVERY part is multiplied by batch_price_multiplier.
    The 1-hour write tokens are in usage.cache_creation.ephemeral_1h_input_tokens
    (cache_creation can be None);
    5-minute write tokens = cache_creation_input_tokens - the 1-hour write tokens. A cache field can be None:
    treat it as 0.
    A model that is not in the config, or has no price_per_mtok / cache_price_per_mtok: raise ValueError.
    Ignore the long prompt price (long_context of Haiku 5.5): the tests use prompts under 100,000 tokens.

so_lan_doc_hoa_von(model, ttl) -> int
    The smallest number of reads n (n >= 1) for which 1 write + n reads is STRICTLY CHEAPER than sending the
    prefix (1 + n) times at the input price.
    ttl is "5m" or "1h"; any other value: raise ValueError.

Grade:  CHAM="$PWD/en/modules/06-cost/exercises" uv run pytest modules/06-cost -q
"""
from __future__ import annotations

from typing import Any

from claude_vi import load_models  # noqa: F401


def chi_phi(msg: Any, batch: bool = False) -> dict[str, float]:
    raise NotImplementedError("TODO: exercise 1")


def so_lan_doc_hoa_von(model: str, ttl: str = "5m") -> int:
    raise NotImplementedError("TODO: exercise 1")
