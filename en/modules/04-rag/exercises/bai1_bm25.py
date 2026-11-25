"""Exercise 1: tokenize Vietnamese, and BM25.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
tach_tu = tokenize, bo_dau = remove accents, tai_lieu = documents (here: tokenized chunks),
tu = word, diem = scores, truy_van = query, tim = search.

tach_tu(text, bo_dau=False) -> list[str]
    1. Normalize with unicodedata.normalize("NFC", ...), then lower-case. (The same letter "ệ" can be typed
       as 1 or 2 Unicode characters; without normalization the two forms do not match.)
    2. bo_dau=True: turn "đ" into "d", then NFD, and remove every character with unicodedata.category == "Mn".
    3. Take tokens with the regex r"\\w+(?:[-.,]\\w+)*": it keeps "e-17", "md-300", "7,00", "26.5" whole.

class BM25(k1=1.5, b=0.75)
    fit(tai_lieu: list[list[str]]) -> self       tai_lieu is the list of tokenized chunks
    idf(tu) = ln(1 + (N - n + 0.5) / (n + 0.5))   N is the number of chunks, n the number that contain the word
    diem(truy_van) -> list[float], one score per chunk:
        the sum over the DISTINCT words of truy_van (a repeated word counts once):
            idf(w) * f * (k1 + 1) / (f + k1 * (1 - b + b * dl / avgdl))
        f: how many times w appears in the chunk (f = 0 adds nothing), dl: the number of tokens in the chunk,
        avgdl: the average number of tokens per chunk.
    tim(truy_van, k=5) -> list[(chunk index, score)]
        the k chunks with the highest scores, without chunks that score 0; on a tie, the smaller index comes first.

Grade:  CHAM="$PWD/en/modules/04-rag/exercises" uv run pytest modules/04-rag -q
"""
from __future__ import annotations

import math  # noqa: F401
import re  # noqa: F401
import unicodedata  # noqa: F401
from collections import Counter  # noqa: F401


def tach_tu(text: str, bo_dau: bool = False) -> list[str]:
    raise NotImplementedError("TODO: exercise 1")


class BM25:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1, self.b = k1, b

    def fit(self, tai_lieu: list[list[str]]) -> BM25:
        raise NotImplementedError("TODO: exercise 1")

    def idf(self, tu: str) -> float:
        raise NotImplementedError("TODO: exercise 1")

    def diem(self, truy_van: list[str]) -> list[float]:
        raise NotImplementedError("TODO: exercise 1")

    def tim(self, truy_van: list[str], k: int = 5) -> list[tuple[int, float]]:
        raise NotImplementedError("TODO: exercise 1")
