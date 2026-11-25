"""Bài 3 — dựng batch đúng luật và gom kết quả theo custom_id.

tao_requests(viec: dict[str, str]) -> list[dict]
    viec: khoá = mã việc do bạn đặt, giá trị = câu hỏi. Mỗi việc thành một request
    {"custom_id": ma, "params": {"messages": [{"role": "user", "content": cau_hoi}]}}, theo thứ tự của dict.
    custom_id phải khớp ^[a-zA-Z0-9_-]{1,64}$ (docs Batch processing). Mã sai: raise ValueError (trước khi gửi).
    Kiểm bằng re.fullmatch: với re.match, `$` của Python vẫn khớp trước ký tự xuống dòng ở cuối ("ok\n").
    viec rỗng: raise ValueError.

gom(ket_qua) -> dict
    ket_qua: iterable các MessageBatchIndividualResponse (thứ tự bất kỳ). Trả về:
    {"tra_loi": {custom_id: text}         # chỉ result "succeeded", lấy text bằng text_of
     "loi": {custom_id: loai}             # "errored", "canceled", "expired"
     "usd": tổng estimate_cost_usd(message, batch=True) của các request succeeded}
    Chỉ succeeded bị tính tiền.

Chấm:  CHAM=exercises uv run pytest modules/06-cost -q
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from claude_vi import estimate_cost_usd, text_of  # noqa: F401


def tao_requests(viec: dict[str, str]) -> list[dict[str, Any]]:
    raise NotImplementedError("TODO: bài 3")


def gom(ket_qua: Iterable[Any]) -> dict[str, Any]:
    raise NotImplementedError("TODO: bài 3")
