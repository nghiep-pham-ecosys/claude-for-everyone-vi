"""Module 04: ask Claude to write the context for each chunk (contextual retrieval).

Send the whole document plus one chunk, and ask for 1–2 sentences that place the chunk in context. That sentence
goes at the front of the chunk before indexing. One call per chunk, and each call sends the whole document again:
for a large collection, use prompt caching for the document part (module 06) and the Batch API to cut the cost.

The script does this for ONE document only, to limit the cost when you run it for real.
The request is built by the shared exercise code, so its prompt is in Vietnamese, like the handbook.

Run:  CLAUDE_MOCK=1 uv run python en/modules/04-rag/python/03_ngu_canh_claude.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "shared" / "py"))
sys.path.insert(0, str(ROOT / "modules" / "04-rag" / "python"))

from claude_vi import ClaudeVi, estimate_cost_usd, text_of  # noqa: E402
from rag_mau import chia, doc_so_tay  # noqa: E402

client = ClaudeVi()
document = doc_so_tay()[0]
total = 0.0
for chunk in chia.chia_doan(document):
    msg = client.create(**chia.yeu_cau_ngu_canh(document, chunk))
    context = text_of(msg).strip() if msg.stop_reason == "end_turn" else ""
    total += estimate_cost_usd(msg)
    print(f"{chunk.id:<20} context: {context!r}\n{'':<20} chunk:   {chunk.noi_dung[:60]!r}")

print(f"\nEstimated cost for {document.ten}: ${total:.6f}. In mock mode the context is '[MOCK]...' and does not help search.")
