"""Exercise 2: count tokens first, and send only when the maximum cost is within budget.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
tran_chi_phi = cost cap, goi_trong_ngan_sach = call within budget, ngan_sach_usd = budget in USD,
VuotNganSach = over budget.

tran_chi_phi(client, params) -> float
    The MAXIMUM cost (USD) of the request `params` (a dict for client.create;
    it may lack "model"/"max_tokens"):
    - model: params["model"] or client.settings.model; max_tokens: params["max_tokens"] or
      client.settings.max_tokens.
    - input: count it with client.count_tokens(...) (take "max_tokens" out first: count_tokens does not accept
      it), priced at the input price (do not assume a cache).
    - Do NOT change the caller's params dict: copy it (dict(params)), then take max_tokens out.
    - output: max_tokens x the output price.
    Prices from load_models()["models"][model]["price_per_mtok"].

goi_trong_ngan_sach(client, params, ngan_sach_usd) -> Message
    tran_chi_phi(...) > ngan_sach_usd: raise VuotNganSach (do NOT call client.create).
    Otherwise: return client.create(**params).
    Each call of this function counts tokens EXACTLY ONCE.

Grade:  CHAM="$PWD/en/modules/06-cost/exercises" uv run pytest modules/06-cost -q
"""
from __future__ import annotations

from typing import Any

from claude_vi import ClaudeVi, load_models  # noqa: F401


class VuotNganSach(Exception):
    """The request could cost more than the allowed budget."""


def tran_chi_phi(client: ClaudeVi, params: dict[str, Any]) -> float:
    raise NotImplementedError("TODO: exercise 2")


def goi_trong_ngan_sach(client: ClaudeVi, params: dict[str, Any], ngan_sach_usd: float) -> Any:
    raise NotImplementedError("TODO: exercise 2")
