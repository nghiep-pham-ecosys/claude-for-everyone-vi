"""Phần nối dùng chung cho các script module 04 (không phải bài học riêng).

Nạp code từ solutions/ (mặc định) hoặc exercises/ nếu đặt CHAM=exercises, nên bạn chạy được
mọi script bằng chính code của mình:  CHAM=exercises CLAUDE_MOCK=1 uv run python .../01_bm25.py
"""
from __future__ import annotations

import sys
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE.parents[1] / "shared" / "py"))

from claude_vi.cham import nap  # noqa: E402

bm25 = nap(MODULE, "bai1_bm25")
chia = nap(MODULE, "bai2_chia_doan")
hop = nap(MODULE, "bai3_hop_nhat")
SO_TAY = MODULE / "data" / "so_tay"


def doc_so_tay() -> list:
    return [chia.TaiLieu(p.stem, p.read_text("utf-8")) for p in sorted(SO_TAY.glob("*.md"))]


def tat_ca_doan(ngu_canh: bool = True) -> tuple[list, list[str]]:
    """(danh sách Doan, text dùng để lập chỉ mục cho từng đoạn)."""
    doan = [d for t in doc_so_tay() for d in chia.chia_doan(t)]
    return doan, [chia.them_ngu_canh(d) if ngu_canh else d.noi_dung for d in doan]


def chi_muc(texts: list[str], bo_dau: bool = False):
    return bm25.BM25().fit([bm25.tach_tu(t, bo_dau) for t in texts])


def tim(doan: list, texts: list[str], cau_hoi: str, k: int = 3) -> list:
    """Hybrid: BM25 có dấu + BM25 không dấu, hợp nhất bằng RRF. Trả k đoạn tốt nhất."""
    co_dau = chi_muc(texts).tim(bm25.tach_tu(cau_hoi), k=20)
    khong_dau = chi_muc(texts, bo_dau=True).tim(bm25.tach_tu(cau_hoi, bo_dau=True), k=20)
    hop_nhat = hop.hop_nhat_rrf([doan[i].id for i, _ in co_dau], [doan[i].id for i, _ in khong_dau])
    theo_id = {d.id: d for d in doan}
    return [theo_id[i] for i, _ in hop_nhat[:k]]
