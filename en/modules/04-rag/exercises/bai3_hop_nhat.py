"""Exercise 3: merge rankings (RRF), pack search_result blocks, read the citations.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
hop_nhat_rrf = merge with RRF, xep_hang = rankings, khoi_ket_qua = result blocks,
nguon_trich_dan = cited sources, doan = chunks.

hop_nhat_rrf(*xep_hang, k=60) -> list[(id, score)]
    Reciprocal Rank Fusion: each xep_hang is a list of ids, best first (rank 1).
    score(id) = the sum, over the lists that contain id, of 1 / (k + rank). Sort by score, highest first;
    on a tie, the id seen first (going through the first list, then the second...) comes first.
    RRF uses only ranks, not the raw scores, so it can merge BM25 with embeddings despite different scales.

khoi_ket_qua(doan, citations=True) -> list[dict]
    Each Doan becomes one block:
        {"type": "search_result", "source": "kb://so-tay/{id}", "title": ..., "content": [...],
         "citations": {"enabled": citations}}
    - title: "{tieu_de} — {muc}", or just tieu_de if muc is empty.
    - content: each non-empty line of noi_dung becomes a block {"type": "text", "text": the stripped line}.
      Claude cites whole blocks, so small blocks give tighter citations.

nguon_trich_dan(msg) -> list[{"source", "title", "cited_text"}]
    The citations of type "search_result_location" in the text blocks, in order, without duplicate
    (source, cited_text) pairs. A None title becomes "". stop_reason other than "end_turn" -> raise ValueError.

Grade:  CHAM="$PWD/en/modules/04-rag/exercises" uv run pytest modules/04-rag -q
"""
from __future__ import annotations

from typing import Any

from anthropic.types import Message


def hop_nhat_rrf(*xep_hang: list[str], k: int = 60) -> list[tuple[str, float]]:
    raise NotImplementedError("TODO: exercise 3")


def khoi_ket_qua(doan: list[Any], citations: bool = True) -> list[dict[str, Any]]:
    raise NotImplementedError("TODO: exercise 3")


def nguon_trich_dan(msg: Message) -> list[dict[str, str]]:
    raise NotImplementedError("TODO: exercise 3")
