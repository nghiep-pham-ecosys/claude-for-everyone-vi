"""Module 04 — nhờ Claude viết ngữ cảnh cho từng đoạn (contextual retrieval).

Gửi cả tài liệu + một đoạn, xin 1–2 câu đặt đoạn đó vào bối cảnh. Câu này được ghép vào đầu đoạn
trước khi lập chỉ mục. Mỗi đoạn một lời gọi, và mỗi lời gọi gửi lại cả tài liệu: với kho lớn, dùng
prompt caching cho phần tài liệu (module 06) và Batch API để giảm chi phí.

Script chỉ làm cho MỘT tài liệu để giới hạn chi phí khi chạy thật.

Chạy:  CLAUDE_MOCK=1 uv run python modules/04-rag/python/03_ngu_canh_claude.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from claude_vi import ClaudeVi, estimate_cost_usd, text_of  # noqa: E402
from rag_mau import chia, doc_so_tay  # noqa: E402

client = ClaudeVi()
tai_lieu = doc_so_tay()[0]
tong = 0.0
for d in chia.chia_doan(tai_lieu):
    msg = client.create(**chia.yeu_cau_ngu_canh(tai_lieu, d))
    ngu_canh = text_of(msg).strip() if msg.stop_reason == "end_turn" else ""
    tong += estimate_cost_usd(msg)
    print(f"{d.id:<20} ngữ cảnh: {ngu_canh!r}\n{'':<20} đoạn:     {d.noi_dung[:60]!r}")

print(f"\nChi phí ước tính cho {tai_lieu.ten}: ${tong:.6f}. Ở mock mode ngữ cảnh là '[MOCK]...', không giúp tìm kiếm.")
