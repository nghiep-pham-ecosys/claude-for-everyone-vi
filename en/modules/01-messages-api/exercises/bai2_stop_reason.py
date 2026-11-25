"""Exercise 2: read stop_reason and add up the cost of a whole conversation.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
nen_lam_gi = what to do, chi_phi_hoi_thoai = conversation cost.

nen_lam_gi(msg) returns ONE of these strings, based on msg.stop_reason:
    end_turn, stop_sequence          -> "dung_ket_qua"                 (use the result)
    max_tokens                       -> "tang_max_tokens"              (raise max_tokens)
    model_context_window_exceeded    -> "rut_gon_lich_su"              (shorten the history)
    tool_use                         -> "chay_tool"                    (run the tool)
    pause_turn                       -> "gui_lai_nguyen_ven"           (send it back unchanged)
    refusal                          -> "doi_model_hoac_dien_dat_lai"  (change the model or rephrase)
    any other value                  -> raise ValueError (do not treat an unknown reason as success)

chi_phi_hoi_thoai(msgs) returns a dict with 4 keys:
    input_tokens, output_tokens, thinking_tokens (from usage.output_tokens_details, can be None), usd
    usd = the sum of estimate_cost_usd(m).

Grade:  CHAM="$PWD/en/modules/01-messages-api/exercises" uv run pytest modules/01-messages-api -q
"""
from __future__ import annotations

from anthropic.types import Message

from claude_vi import estimate_cost_usd  # noqa: F401


def nen_lam_gi(msg: Message) -> str:
    raise NotImplementedError("TODO: exercise 2")


def chi_phi_hoi_thoai(msgs: list[Message]) -> dict[str, float]:
    raise NotImplementedError("TODO: exercise 2")
