"""Module 04: give the chunks you found to Claude as search_result blocks, and get an answer with citations.

A search_result block has a source (a stable ID for the chunk) and a title that you set. With citations on,
each claim in the answer points to the exact text block it used, with its source: you can show it as a link.

The question is in English; the handbook is in Vietnamese. BM25 still finds the right chunk,
because the codes "MD-300" and "E-17" are the same in both languages.

Run:  CLAUDE_MOCK=1 uv run python en/modules/04-rag/python/04_search_result.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "shared" / "py"))
sys.path.insert(0, str(ROOT / "modules" / "04-rag" / "python"))

from claude_vi import ClaudeVi, estimate_cost_usd, text_of  # noqa: E402
from rag_mau import hop, tat_ca_doan, tim  # noqa: E402

QUESTION = "The MD-300 meter shows E-17. What should I do?"
chunks, texts = tat_ca_doan()
found = tim(chunks, texts, QUESTION, k=3)
print("Chunks found:", [c.id for c in found])

msg = ClaudeVi().create(
    system=("You answer questions from lab staff using only the search results from the handbook. "
            "The handbook is in Vietnamese; answer in English. "
            "If there is no information, say so, because a wrong procedure can damage the equipment."),
    messages=[{"role": "user", "content": [*hop.khoi_ket_qua(found), {"type": "text", "text": QUESTION}]}],
)
print("\nAnswer:", text_of(msg))
print("\nSources:")
for n in hop.nguon_trich_dan(msg):
    print(f"  {n['source']:<32} {n['cited_text']!r}")
print(f"\nEstimated cost: ${estimate_cost_usd(msg):.6f}")
