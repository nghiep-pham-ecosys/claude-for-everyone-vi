"""Bài 1 — tách từ tiếng Việt và BM25.

tach_tu(text, bo_dau=False) -> list[str]
    1. Chuẩn hoá unicodedata.normalize("NFC", ...) rồi chữ thường. (Cùng chữ "ệ" có thể được gõ
       thành 1 hoặc 2 ký tự Unicode; không chuẩn hoá thì hai cách gõ không khớp nhau.)
    2. bo_dau=True: đổi "đ" thành "d", rồi NFD và bỏ mọi ký tự có unicodedata.category == "Mn".
    3. Lấy token bằng regex r"\\w+(?:[-.,]\\w+)*": giữ nguyên "e-17", "md-300", "7,00", "26.5".

class BM25(k1=1.5, b=0.75)
    fit(tai_lieu: list[list[str]]) -> self       tai_lieu là danh sách đoạn đã tách từ
    idf(tu) = ln(1 + (N - n + 0.5) / (n + 0.5))   N số đoạn, n số đoạn chứa từ
    diem(truy_van) -> list[float], một điểm cho mỗi đoạn:
        tổng trên các từ KHÁC NHAU của truy_van (từ lặp chỉ tính một lần):
            idf(w) * f * (k1 + 1) / (f + k1 * (1 - b + b * dl / avgdl))
        f: số lần w xuất hiện trong đoạn (f = 0 thì không cộng), dl: số token của đoạn,
        avgdl: số token trung bình của các đoạn.
    tim(truy_van, k=5) -> list[(chỉ số đoạn, điểm)]
        k đoạn điểm cao nhất, bỏ đoạn điểm 0; bằng điểm thì chỉ số nhỏ đứng trước.

Chấm:  CHAM=exercises uv run pytest modules/04-rag -q
"""
from __future__ import annotations

import math  # noqa: F401
import re  # noqa: F401
import unicodedata  # noqa: F401
from collections import Counter  # noqa: F401


def tach_tu(text: str, bo_dau: bool = False) -> list[str]:
    raise NotImplementedError("TODO: bài 1")


class BM25:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1, self.b = k1, b

    def fit(self, tai_lieu: list[list[str]]) -> BM25:
        raise NotImplementedError("TODO: bài 1")

    def idf(self, tu: str) -> float:
        raise NotImplementedError("TODO: bài 1")

    def diem(self, truy_van: list[str]) -> list[float]:
        raise NotImplementedError("TODO: bài 1")

    def tim(self, truy_van: list[str], k: int = 5) -> list[tuple[int, float]]:
        raise NotImplementedError("TODO: bài 1")
