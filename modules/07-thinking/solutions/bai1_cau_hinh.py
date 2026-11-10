"""Bài 1 — chọn cấu hình thinking theo luật từng model. (LỜI GIẢI)"""
from __future__ import annotations

from typing import Any

from claude_vi import load_models


def _rules(model: str) -> dict[str, Any]:
    entry = load_models()["models"].get(model)
    if entry is None or entry.get("status") != "active":
        raise ValueError(f"Model '{model}' không active trong config/models.yaml")
    return entry.get("rules", {})


def it_thinking_nhat(model: str) -> dict[str, Any]:
    rules = _rules(model)
    params: dict[str, Any] = {"output_config": {"effort": "low"}}
    if rules.get("thinking_disabled_allowed"):
        params["thinking"] = {"type": "disabled"}
    elif rules.get("between_tools_allowed"):
        params["thinking"] = {"type": "between_tools"}
    return params


def xem_tom_tat(model: str, effort: str | None = None) -> dict[str, Any]:
    _rules(model)
    params: dict[str, Any] = {"thinking": {"type": "adaptive", "display": "summarized"}}
    if effort is not None:
        params["output_config"] = {"effort": effort}
    return params
