"""Module 08 — ba nấc: một lời gọi, workflow, agent. Bắt đầu từ nấc thấp nhất.

Cùng một việc, làm theo hai cách:
  A. một lời gọi (tài liệu đặt trong prompt, như RAG ở module 04);
  B. workflow hai bước: trích dữ kiện, rồi viết câu trả lời từ dữ kiện.
In số lời gọi, token và chi phí của mỗi cách. Nấc thứ ba, agent, ở script 07.

Chạy:  CLAUDE_MOCK=1 uv run python modules/08-agents-workflows/python/01_mot_loi_goi.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from phong_thi_nghiem import SoChiPhi, doc_trang, tao_client  # noqa: E402

from claude_vi import text_of  # noqa: E402

client = tao_client()
tai_lieu = doc_trang("01_hieu_chuan_ph")
cau_hoi = "Hiệu chuẩn máy đo pH cần mấy dung dịch đệm, và sau bao lâu phải hiệu chuẩn lại?"

# A. Một lời gọi: đủ cho hầu hết câu hỏi có sẵn tài liệu
so_a = SoChiPhi()
msg = so_a.ghi(client.ask(f"<tai_lieu>\n{tai_lieu}\n</tai_lieu>\n\n{cau_hoi}",
                          system="Trả lời ngắn, chỉ dựa vào tài liệu."))
print("A. Một lời gọi:", text_of(msg)[:80])
print("  ", so_a.bao_cao())

# B. Workflow hai bước: đường đi do code quyết, không phải do Claude
so_b = SoChiPhi()
buoc1 = so_b.ghi(client.ask(f"<tai_lieu>\n{tai_lieu}\n</tai_lieu>\n\nLiệt kê các dữ kiện liên quan tới: {cau_hoi}",
                            system="Chỉ liệt kê dữ kiện có trong tài liệu, mỗi dòng một ý."))
buoc2 = so_b.ghi(client.ask(f"<du_kien>\n{text_of(buoc1)}\n</du_kien>\n\n{cau_hoi}",
                            system="Trả lời ngắn, chỉ dựa vào dữ kiện."))
print("\nB. Workflow hai bước:", text_of(buoc2)[:80])
print("  ", so_b.bao_cao())

print("\nCách B tốn gấp đôi số lời gọi. Chỉ đáng khi đo được là nó tốt hơn cách A trên chính bài toán của bạn."
      "\nAgent (Claude tự chọn bước tiếp theo) còn đắt và khó kiểm hơn nữa: xem script 07.")
