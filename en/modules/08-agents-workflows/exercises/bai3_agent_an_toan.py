"""Exercise 3: an agent loop with a turn cap, a cost cap, an approval step and a trace.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
chay_agent = run the agent, cau_hoi = question, duyet = approve, can_duyet = needs approval,
toi_da_luot = max turns, tran_usd = cost cap in USD, tran_mot_loi_goi = cap of one call,
ly_do_dung = stop reason, so_loi_goi = number of calls, luot = turn, ghi_nhat_ky = write to the log.
The stop reasons: tran_chi_phi = cost cap, het_luot = out of turns.

chay_agent(client, cau_hoi, tools, registry, duyet, *, can_duyet, toi_da_luot, tran_usd, trace) -> dict
    Returns {"ly_do_dung", "msg", "so_loi_goi", "usd", "messages"}:
      ly_do_dung: "tran_chi_phi", "het_luot", or the stop_reason of the last call when it is not "tool_use"
                  ("end_turn", "max_tokens", "refusal"...);
      msg: the last Message (None if no call was made); usd: the sum of estimate_cost_usd over EVERY call;
      messages: the history that was sent.

    Each turn, in this order:
    1. BEFORE the call: usd + tran_mot_loi_goi(client) > tran_usd -> stop with "tran_chi_phi".
    2. msg = client.create(messages=messages, tools=tools). Add the cost. If trace is a list: append ONE dict
       {"luot", "stop_reason", "tools" (the names of the tool_use blocks), "input_tokens", "output_tokens", "usd"}.
    3. stop_reason other than "tool_use" -> stop with that same stop_reason.
    4. Append the assistant turn with msg.content UNTOUCHED (the mock returns 400 if you drop or edit
       a thinking block).
    5. ONE user turn with a tool_result for EVERY tool_use, in order:
       - a name not in `tools` or not in `registry` -> is_error, the content lists the tools available;
       - a name in can_duyet where duyet(name, input) returns False -> is_error, the content says it was refused;
         the tool is NOT run;
       - the tool raises an exception -> is_error, content "<ErrorName>: <message>";
       - otherwise: the content is the result (a string as is, any other type through json.dumps).
    After toi_da_luot calls that still end in "tool_use" -> stop with "het_luot".

Grade:  CHAM="$PWD/en/modules/08-agents-workflows/exercises" uv run pytest modules/08-agents-workflows -q
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from claude_vi import ClaudeVi, estimate_cost_usd, load_models  # noqa: F401


def tran_mot_loi_goi(client: ClaudeVi) -> float:
    """The highest output cost of one call with the client's model and default max_tokens."""
    gia = load_models()["models"][client.settings.model]["price_per_mtok"]
    return client.settings.max_tokens * gia["output"] / 1_000_000


def chay_agent(client: ClaudeVi, cau_hoi: str, tools: list[dict[str, Any]],
               registry: dict[str, Callable[..., Any]], duyet: Callable[[str, dict[str, Any]], bool], *,
               can_duyet: frozenset[str] = frozenset({"ghi_nhat_ky"}), toi_da_luot: int = 6,
               tran_usd: float = 0.01, trace: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    raise NotImplementedError("TODO: exercise 3")
