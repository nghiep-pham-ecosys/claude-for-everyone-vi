"""Module 04 — đưa đoạn tìm được cho Claude dưới dạng search_result, nhận câu trả lời có trích dẫn.

Block search_result có source (mã ổn định của đoạn) và title do bạn đặt. Bật citations thì mỗi khẳng định
trong câu trả lời trỏ về đúng khối text đã dùng, kèm source — hiển thị được thành link cho người dùng.

Chạy:  CLAUDE_MOCK=1 uv run python modules/04-rag/python/04_search_result.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from claude_vi import ClaudeVi, estimate_cost_usd, text_of  # noqa: E402
from rag_mau import hop, tat_ca_doan, tim  # noqa: E402

CAU_HOI = "Máy MD-300 báo E-17 thì phải làm gì?"
doan, texts = tat_ca_doan()
tim_duoc = tim(doan, texts, CAU_HOI, k=3)
print("Đoạn tìm được:", [d.id for d in tim_duoc])

msg = ClaudeVi().create(
    system=("Bạn trả lời câu hỏi của nhân viên phòng thí nghiệm chỉ dựa trên kết quả tìm kiếm trong sổ tay. "
            "Không có thông tin thì nói không có, vì trả lời sai quy trình có thể làm hỏng thiết bị."),
    messages=[{"role": "user", "content": [*hop.khoi_ket_qua(tim_duoc), {"type": "text", "text": CAU_HOI}]}],
)
print("\nTrả lời:", text_of(msg))
print("\nNguồn:")
for n in hop.nguon_trich_dan(msg):
    print(f"  {n['source']:<32} {n['cited_text']!r}")
print(f"\nChi phí ước tính: ${estimate_cost_usd(msg):.6f}")
