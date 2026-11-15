"""Module 04 — vì sao đoạn cần ngữ cảnh.

Cắt tài liệu thành đoạn làm mất thông tin: đoạn "Thực hiện lại sau mỗi 8 giờ đo..." không nhắc
"hiệu chuẩn" hay "pH", vì tên đó nằm ở tiêu đề. Câu hỏi "bao lâu phải hiệu chuẩn máy pH" khó tìm ra nó.
Cách rẻ nhất: chép tiêu đề tài liệu và tên mục vào đầu mỗi đoạn trước khi lập chỉ mục.

Chạy:  CLAUDE_MOCK=1 uv run python modules/04-rag/python/02_ngu_canh.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rag_mau import bm25, chi_muc, tat_ca_doan  # noqa: E402

CAU_HOI = "bao lâu phải hiệu chuẩn lại máy đo pH"
DUNG = "01_hieu_chuan_ph#4"          # mục "Tần suất"

for ngu_canh in (False, True):
    doan, texts = tat_ca_doan(ngu_canh=ngu_canh)
    ket_qua = chi_muc(texts).tim(bm25.tach_tu(CAU_HOI), k=len(doan))
    hang = next((h for h, (i, _) in enumerate(ket_qua, 1) if doan[i].id == DUNG), None)
    print(f"== {'CÓ' if ngu_canh else 'KHÔNG CÓ'} tiêu đề/mục ở đầu đoạn: đoạn đúng xếp hạng {hang}")
    for i, s in ket_qua[:3]:
        print(f"  {s:5.2f}  {doan[i].id:<22} {texts[i][:70]!r}")

print("\nTiêu đề giúp đoạn đúng leo hạng, nhưng câu hỏi nói 'bao lâu' còn mục tên 'Tần suất': BM25 không biết"
      "\nhai cách nói này cùng nghĩa. Lấy top-5 thay vì top-3, hoặc thêm ngữ cảnh do Claude viết, sẽ bù được.")
print("\nBài blog Contextual Retrieval của Anthropic đi xa hơn: nhờ Claude viết 1–2 câu ngữ cảnh"
      "\ncho từng đoạn (script 03). Đo trên câu hỏi thật của bạn trước khi trả tiền cho bước đó.")
