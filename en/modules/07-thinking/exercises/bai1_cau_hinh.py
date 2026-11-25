"""Exercise 1: choose the thinking setup by the rules of each model.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
cau_hinh = setup, it_thinking_nhat = least thinking, xem_tom_tat = see the summary.

Read the rules from config/models.yaml with load_models()["models"][model]["rules"]. Do NOT hard-code model
names: when a new model comes out, only the YAML changes, and your code is still right.

it_thinking_nhat(model) -> a dict of parameters for client.create(**...) so the model thinks as little as possible
    - Always has "output_config": {"effort": "low"}.
    - If rules["thinking_disabled_allowed"]: add "thinking": {"type": "disabled"}.
    - Otherwise, if rules["between_tools_allowed"]: add "thinking": {"type": "between_tools"}.
    - Otherwise: no thinking field (the model cannot turn thinking off; effort is the only knob).

xem_tom_tat(model, effort=None) -> a dict to read the thinking summary
    - "thinking": {"type": "adaptive", "display": "summarized"}
    - if effort is not None, add "output_config": {"effort": effort}.

Both: a model that is not in the YAML, or whose status is not "active" -> raise ValueError.

Grade:  CHAM="$PWD/en/modules/07-thinking/exercises" uv run pytest modules/07-thinking -q
"""
from __future__ import annotations

from typing import Any

from claude_vi import load_models  # noqa: F401


def it_thinking_nhat(model: str) -> dict[str, Any]:
    raise NotImplementedError("TODO: exercise 1")


def xem_tom_tat(model: str, effort: str | None = None) -> dict[str, Any]:
    raise NotImplementedError("TODO: exercise 1")
