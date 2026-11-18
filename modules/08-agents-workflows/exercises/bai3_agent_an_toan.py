"""Bài 3 — vòng lặp agent có trần lượt, trần chi phí, bước duyệt và trace.

chay_agent(client, cau_hoi, tools, registry, duyet, *, can_duyet, toi_da_luot, tran_usd, trace) -> dict
    Trả {"ly_do_dung", "msg", "so_loi_goi", "usd", "messages"}:
      ly_do_dung: "tran_chi_phi", "het_luot", hoặc stop_reason của lời gọi cuối khi nó khác "tool_use"
                  ("end_turn", "max_tokens", "refusal"...);
      msg: Message cuối (None nếu chưa gọi lần nào); usd: tổng estimate_cost_usd của MỌI lời gọi;
      messages: lịch sử đã gửi.

    Mỗi lượt, theo thứ tự:
    1. TRƯỚC khi gọi: usd + tran_mot_loi_goi(client) > tran_usd -> dừng "tran_chi_phi".
    2. msg = client.create(messages=messages, tools=tools). Cộng chi phí. Nếu trace là list: thêm MỘT dict
       {"luot", "stop_reason", "tools" (tên các tool_use), "input_tokens", "output_tokens", "usd"}.
    3. stop_reason khác "tool_use" -> dừng với chính stop_reason đó.
    4. Nối lượt assistant với msg.content NGUYÊN VẸN (mock trả 400 nếu bỏ hoặc sửa block thinking).
    5. MỘT lượt user chứa tool_result cho MỌI tool_use, đúng thứ tự:
       - tên không có trong `tools` hoặc không có trong `registry` -> is_error, content nêu các tool hiện có;
       - tên trong can_duyet mà duyet(ten, input) trả False -> is_error, content nói bị từ chối;
         tool KHÔNG được chạy;
       - tool ném exception -> is_error, content "<TênLỗi>: <thông điệp>";
       - còn lại: content là kết quả (chuỗi giữ nguyên, kiểu khác thì json.dumps).
    Hết toi_da_luot lần gọi mà vẫn "tool_use" -> dừng "het_luot".

Chấm:  CHAM=exercises uv run pytest modules/08-agents-workflows -q
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from claude_vi import ClaudeVi, estimate_cost_usd, load_models  # noqa: F401


def tran_mot_loi_goi(client: ClaudeVi) -> float:
    """Chi phí output tối đa của một lời gọi với model và max_tokens mặc định của client."""
    gia = load_models()["models"][client.settings.model]["price_per_mtok"]
    return client.settings.max_tokens * gia["output"] / 1_000_000


def chay_agent(client: ClaudeVi, cau_hoi: str, tools: list[dict[str, Any]],
               registry: dict[str, Callable[..., Any]], duyet: Callable[[str, dict[str, Any]], bool], *,
               can_duyet: frozenset[str] = frozenset({"ghi_nhat_ky"}), toi_da_luot: int = 6,
               tran_usd: float = 0.01, trace: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    raise NotImplementedError("TODO: bài 3")
