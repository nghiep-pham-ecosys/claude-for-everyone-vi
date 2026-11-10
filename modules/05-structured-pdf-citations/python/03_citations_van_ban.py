"""Module 05 — citations trên tài liệu văn bản thuần.

Bật citations.enabled trên document. Response chia thành nhiều block text; block nào chứa
một khẳng định có nguồn thì kèm danh sách citations. Với văn bản thuần, vị trí là chỉ số ký tự
(từ 0, end không tính), nên ta tự kiểm được: tai_lieu[start:end] phải đúng bằng cited_text.

Chạy:  CLAUDE_MOCK=1 uv run python modules/05-structured-pdf-citations/python/03_citations_van_ban.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from claude_vi import ClaudeVi  # noqa: E402

# Số liệu bịa, dùng cho bài học
TAI_LIEU = (
    "Phiếu quan trắc giếng khoan GK-03, lấy mẫu ngày 12/10/2026. "
    "Mẫu W1 có pH 7.1 và DO 6.2 mg/L. "
    "Mẫu W2 có độ đục 12 NTU và pH 6.4. "
    "Người lấy mẫu ghi chú trời mưa nhẹ."
)

msg = ClaudeVi().create(messages=[{"role": "user", "content": [
    {"type": "document", "title": "Phiếu GK-03", "context": "Phiếu nội bộ, số liệu bịa cho bài học",
     "source": {"type": "text", "media_type": "text/plain", "data": TAI_LIEU},
     "citations": {"enabled": True}},
    {"type": "text", "text": "Mẫu nào có pH thấp hơn 7? Trích nguồn cho mỗi số liệu."},
]}])

for block in msg.content:
    if block.type != "text":
        continue
    print(f"TEXT  {block.text!r}")
    for c in block.citations or []:
        khop = TAI_LIEU[c.start_char_index:c.end_char_index] == c.cited_text
        print(f"  └─ {c.type} tài liệu {c.document_index} ký tự {c.start_char_index}–{c.end_char_index} "
              f"{'khớp' if khop else 'KHÔNG KHỚP'}: {c.cited_text!r}")

print("\n`title` và `context` được gửi cho Claude nhưng không bao giờ được trích dẫn.")
