"""Module 05 — gửi PDF cho Claude.

Ba cách đưa PDF vào block document: base64 (script này), URL, hoặc file_id từ Files API.
API chuyển mỗi trang thành ảnh và rút text, nên mỗi trang tốn cả token text lẫn token ảnh.

Chạy:  CLAUDE_MOCK=1 uv run python modules/05-structured-pdf-citations/python/02_pdf.py
"""
import base64
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared" / "py"))

from claude_vi import ClaudeVi, estimate_cost_usd, text_of  # noqa: E402
from pypdf import PdfReader  # noqa: E402

pdf = (ROOT / "capstones" / "c2-trich-xuat-pdf" / "data" / "bao_cao_thi_nghiem.pdf").read_bytes()
so_trang = len(PdfReader(io.BytesIO(pdf)).pages)
print(f"PDF {len(pdf):,} byte, {so_trang} trang. Ước tính phần text: {so_trang * 1500:,}–{so_trang * 3000:,} token, "
      "chưa tính token ảnh. Muốn số chính xác thì dùng token counting.")

msg = ClaudeVi().create(messages=[{"role": "user", "content": [
    # PDF đặt TRƯỚC câu hỏi (docs PDF support)
    {"type": "document", "title": "Báo cáo thí nghiệm",
     "source": {"type": "base64", "media_type": "application/pdf", "data": base64.b64encode(pdf).decode()}},
    {"type": "text", "text": "Báo cáo có mấy thí nghiệm? Mỗi thí nghiệm đo gì? Trả lời 3 câu."},
]}])
print("\nTrả lời:", text_of(msg))
print(f"Token: {msg.usage.input_tokens} vào / {msg.usage.output_tokens} ra, ước tính ${estimate_cost_usd(msg):.6f}")

print("\nHai cách khác, cùng block document (script không gửi):")
print('  URL:      {"type": "url", "url": "https://.../bao_cao.pdf"}')
print('  Files API: {"type": "file", "file_id": "file_..."}   # tải lên một lần, dùng lại nhiều request')
