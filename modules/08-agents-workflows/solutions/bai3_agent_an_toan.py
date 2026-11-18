"""Bài 3 — vòng lặp agent có trần lượt, trần chi phí, bước duyệt và trace. (LỜI GIẢI)"""
from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from claude_vi import ClaudeVi, estimate_cost_usd, load_models


def tran_mot_loi_goi(client: ClaudeVi) -> float:
    """Chi phí output tối đa của một lời gọi với model và max_tokens mặc định của client."""
    gia = load_models()["models"][client.settings.model]["price_per_mtok"]
    return client.settings.max_tokens * gia["output"] / 1_000_000


def _ket_qua(tool_use_id: str, noi_dung: Any, is_error: bool = False) -> dict[str, Any]:
    block = {"type": "tool_result", "tool_use_id": tool_use_id,
             "content": noi_dung if isinstance(noi_dung, str) else json.dumps(noi_dung, ensure_ascii=False)}
    if is_error:
        block["is_error"] = True
    return block


def chay_agent(client: ClaudeVi, cau_hoi: str, tools: list[dict[str, Any]],
               registry: dict[str, Callable[..., Any]], duyet: Callable[[str, dict[str, Any]], bool], *,
               can_duyet: frozenset[str] = frozenset({"ghi_nhat_ky"}), toi_da_luot: int = 6,
               tran_usd: float = 0.01, trace: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    cho_phep = {t["name"] for t in tools} & set(registry)
    messages: list[dict[str, Any]] = [{"role": "user", "content": cau_hoi}]
    usd, so_loi_goi, msg = 0.0, 0, None

    def xong(ly_do: str) -> dict[str, Any]:
        return {"ly_do_dung": ly_do, "msg": msg, "so_loi_goi": so_loi_goi, "usd": usd, "messages": messages}

    for luot in range(1, toi_da_luot + 1):
        if usd + tran_mot_loi_goi(client) > tran_usd:
            return xong("tran_chi_phi")
        msg = client.create(messages=messages, tools=tools)
        so_loi_goi += 1
        usd += estimate_cost_usd(msg)
        if trace is not None:
            trace.append({"luot": luot, "stop_reason": msg.stop_reason,
                          "tools": [b.name for b in msg.content if b.type == "tool_use"],
                          "input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens,
                          "usd": estimate_cost_usd(msg)})
        if msg.stop_reason != "tool_use":
            return xong(msg.stop_reason)
        messages.append({"role": "assistant", "content": msg.content})
        ket_qua = []
        for b in msg.content:
            if b.type != "tool_use":
                continue
            if b.name not in cho_phep:
                ket_qua.append(_ket_qua(b.id, f"Không có tool '{b.name}'. Tool hiện có: "
                                              f"{', '.join(sorted(cho_phep))}.", True))
            elif b.name in can_duyet and not duyet(b.name, b.input):
                ket_qua.append(_ket_qua(b.id, f"Người phụ trách từ chối '{b.name}'. Không thử lại; báo người dùng.",
                                        True))
            else:
                try:
                    ket_qua.append(_ket_qua(b.id, registry[b.name](**b.input)))
                except Exception as e:  # noqa: BLE001 - mọi lỗi của tool đều phải về tay Claude
                    ket_qua.append(_ket_qua(b.id, f"{type(e).__name__}: {e}", True))
        messages.append({"role": "user", "content": ket_qua})
    return xong("het_luot")
