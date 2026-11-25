"""Module 04: why chunks need context (ngu_canh = context).

Chunking loses information: the chunk "Thực hiện lại sau mỗi 8 giờ đo..." ("Repeat after every 8 hours
of measuring...") does not mention "calibration" or "pH", because those words are in the title. The question
"how often must I recalibrate the pH meter" has a hard time finding it.
The cheapest fix: copy the document title and section name to the front of each chunk before indexing.

Run:  CLAUDE_MOCK=1 uv run python en/modules/04-rag/python/02_ngu_canh.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "modules" / "04-rag" / "python"))

from rag_mau import bm25, chi_muc, tat_ca_doan  # noqa: E402

QUESTION = "bao lâu phải hiệu chuẩn lại máy đo pH"   # "how often must I recalibrate the pH meter"
RIGHT = "01_hieu_chuan_ph#4"                         # the section "Tần suất" ("Frequency")

print(f"? {QUESTION}   (how often must I recalibrate the pH meter)\n")
for with_context in (False, True):
    chunks, texts = tat_ca_doan(ngu_canh=with_context)
    results = chi_muc(texts).tim(bm25.tach_tu(QUESTION), k=len(chunks))
    rank = next((r for r, (i, _) in enumerate(results, 1) if chunks[i].id == RIGHT), None)
    print(f"== {'WITH' if with_context else 'WITHOUT'} title/section at the front: the right chunk is at rank {rank}")
    for i, s in results[:3]:
        print(f"  {s:5.2f}  {chunks[i].id:<22} {texts[i][:70]!r}")

print("\nThe title helps the right chunk climb, but the question says 'how often' while the section is called"
      "\n'Frequency': BM25 does not know these mean the same. Taking the top 5 instead of the top 3, or adding"
      "\ncontext written by Claude, makes up for it.")
print("\nAnthropic's Contextual Retrieval blog post goes further: Claude writes 1–2 context sentences"
      "\nfor each chunk (script 03). Measure on your real questions before you pay for that step.")
