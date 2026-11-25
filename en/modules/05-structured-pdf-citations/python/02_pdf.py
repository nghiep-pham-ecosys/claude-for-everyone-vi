"""Module 05: send a PDF to Claude.

Three ways to put a PDF in a document block: base64 (this script), a URL, or a file_id from the Files API.
The API turns each page into an image and extracts its text, so each page costs both text tokens and
image tokens.

Run:  CLAUDE_MOCK=1 uv run python en/modules/05-structured-pdf-citations/python/02_pdf.py
"""
import base64
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "shared" / "py"))

from claude_vi import ClaudeVi, estimate_cost_usd, text_of  # noqa: E402
from pypdf import PdfReader  # noqa: E402

pdf = (ROOT / "capstones" / "c2-trich-xuat-pdf" / "data" / "bao_cao_thi_nghiem.pdf").read_bytes()
pages = len(PdfReader(io.BytesIO(pdf)).pages)
print(f"PDF {len(pdf):,} bytes, {pages} pages. Estimated text part: {pages * 1500:,}–{pages * 3000:,} tokens, "
      "not counting image tokens. For an exact number, use token counting.")

msg = ClaudeVi().create(messages=[{"role": "user", "content": [
    # the PDF goes BEFORE the question (PDF support docs)
    {"type": "document", "title": "Lab report",
     "source": {"type": "base64", "media_type": "application/pdf", "data": base64.b64encode(pdf).decode()}},
    {"type": "text", "text": "How many experiments are in the report? What does each one measure? "
                             "Answer in 3 sentences."},
]}])
print("\nAnswer:", text_of(msg))
print(f"Tokens: {msg.usage.input_tokens} in / {msg.usage.output_tokens} out, "
      f"estimated ${estimate_cost_usd(msg):.6f}")

print("\nTwo other ways, with the same document block (this script does not send them):")
print('  URL:       {"type": "url", "url": "https://.../report.pdf"}')
print('  Files API: {"type": "file", "file_id": "file_..."}   # upload once, reuse in many requests')
