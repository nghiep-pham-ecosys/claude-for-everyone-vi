"""Module 04 — tìm kiếm từ khoá bằng BM25, không cần API, không cần model embedding.

BM25 chấm điểm một đoạn theo các từ của câu hỏi: từ hiếm (như "e-17") nặng ký hơn từ phổ biến
(như "máy"), từ lặp nhiều lần được cộng nhưng có trần, đoạn dài bị trừ bớt.
Nó mạnh ở đúng chỗ embedding hay hụt: mã lỗi, mã thiết bị, con số, thuật ngữ chính xác.

Chạy:  CLAUDE_MOCK=1 uv run python modules/04-rag/python/01_bm25.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rag_mau import bm25, chi_muc, tat_ca_doan  # noqa: E402

doan, texts = tat_ca_doan(ngu_canh=False)
idx = chi_muc(texts)
print(f"{len(doan)} đoạn từ sổ tay. Tách từ: {bm25.tach_tu('Lỗi E-17 trên MD-300, đệm pH 7,00')}\n")

for cau_hoi in ["E-17", "TB-07 là máy gì", "hieu chuan may do pH"]:
    print(f"? {cau_hoi}")
    ket_qua = idx.tim(bm25.tach_tu(cau_hoi), k=2)
    for i, s in ket_qua:
        print(f"  {s:5.2f}  {doan[i].id:<22} {doan[i].noi_dung[:60]!r}")
    if not ket_qua:
        print("  (không tìm thấy)")

print("\nCâu cuối gõ không dấu: 'hieu', 'chuan', 'may', 'do' không khớp 'hiệu', 'chuẩn', 'máy', 'đo';"
      "\nchỉ 'ph' khớp, nên kết quả gần như ngẫu nhiên. Bỏ dấu cả câu hỏi lẫn chỉ mục:")
khong_dau = chi_muc(texts, bo_dau=True)
for i, s in khong_dau.tim(bm25.tach_tu("hieu chuan may do pH", bo_dau=True), k=2):
    print(f"  {s:5.2f}  {doan[i].id:<22} {doan[i].noi_dung[:60]!r}")
print("\nKhông cần gọi Claude ở bước tìm kiếm. Script này không tốn token nào.")
