"""Bài 1 — tách từ tiếng Việt và BM25. (LỜI GIẢI)"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter

_TOKEN = re.compile(r"\w+(?:[-.,]\w+)*")


def tach_tu(text: str, bo_dau: bool = False) -> list[str]:
    text = unicodedata.normalize("NFC", text).lower()
    if bo_dau:
        text = text.replace("đ", "d")
        text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return _TOKEN.findall(text)


class BM25:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1, self.b = k1, b
        self.tf: list[Counter[str]] = []
        self.dl: list[int] = []
        self.df: Counter[str] = Counter()
        self.avgdl = 0.0

    def fit(self, tai_lieu: list[list[str]]) -> BM25:
        self.tf = [Counter(t) for t in tai_lieu]
        self.dl = [len(t) for t in tai_lieu]
        self.df = Counter(w for t in tai_lieu for w in set(t))
        self.avgdl = sum(self.dl) / len(self.dl) if self.dl else 0.0
        return self

    def idf(self, tu: str) -> float:
        n, big_n = self.df.get(tu, 0), len(self.tf)
        return math.log(1 + (big_n - n + 0.5) / (n + 0.5))

    def diem(self, truy_van: list[str]) -> list[float]:
        ket_qua = []
        for tf, dl in zip(self.tf, self.dl, strict=True):
            s = 0.0
            for w in dict.fromkeys(truy_van):
                f = tf.get(w, 0)
                if f:
                    s += self.idf(w) * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            ket_qua.append(s)
        return ket_qua

    def tim(self, truy_van: list[str], k: int = 5) -> list[tuple[int, float]]:
        diem = self.diem(truy_van)
        thu_tu = sorted(range(len(diem)), key=lambda i: (-diem[i], i))
        return [(i, diem[i]) for i in thu_tu if diem[i] > 0][:k]
