"""Module 04: keyword search with BM25. No API, no embedding model.

BM25 scores a chunk by the words in the question: rare words (like "e-17") weigh more than common words
(like "máy", "machine"), repeated words add more but up to a cap, and long chunks are scored down.
It is strong exactly where embeddings tend to miss: error codes, device codes, numbers, exact terms.

The sample handbook is in Vietnamese, so the queries are too; each one is printed with an English gloss.
The search code (rag_mau.py) is shared with the Vietnamese module.

Run:  CLAUDE_MOCK=1 uv run python en/modules/04-rag/python/01_bm25.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "modules" / "04-rag" / "python"))

from rag_mau import bm25, chi_muc, tat_ca_doan  # noqa: E402

chunks, texts = tat_ca_doan(ngu_canh=False)
idx = chi_muc(texts)
print(f"{len(chunks)} chunks from the handbook. Tokens: {bm25.tach_tu('Lỗi E-17 trên MD-300, đệm pH 7,00')}\n")

queries = [
    ("E-17", "an error code"),
    ("TB-07 là máy gì", "what machine is TB-07"),
    ("hieu chuan may do pH", "calibrate the pH meter, typed without accents"),
]
for query, gloss in queries:
    print(f"? {query}   ({gloss})")
    results = idx.tim(bm25.tach_tu(query), k=2)
    for i, s in results:
        print(f"  {s:5.2f}  {chunks[i].id:<22} {chunks[i].noi_dung[:60]!r}")
    if not results:
        print("  (nothing found)")

print("\nThe last query has no accents: 'hieu', 'chuan', 'may', 'do' do not match 'hiệu', 'chuẩn', 'máy', 'đo';"
      "\nonly 'ph' matches, so the result is close to random. Remove the accents from both the query and the index:")
no_accents = chi_muc(texts, bo_dau=True)
for i, s in no_accents.tim(bm25.tach_tu("hieu chuan may do pH", bo_dau=True), k=2):
    print(f"  {s:5.2f}  {chunks[i].id:<22} {chunks[i].noi_dung[:60]!r}")
print("\nThe search step does not need Claude. This script uses no tokens at all.")
