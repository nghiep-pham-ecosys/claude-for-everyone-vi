"""Module 05: citations on a plain text document (van_ban = text).

Turn on citations.enabled on the document. The response is split into several text blocks; a block that
holds a claim with a source carries a list of citations. For plain text, the location is a character index
(from 0, end excluded), so we can check it ourselves: document[start:end] must equal cited_text.

Run:  CLAUDE_MOCK=1 uv run python en/modules/05-structured-pdf-citations/python/03_citations_van_ban.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))

from claude_vi import ClaudeVi  # noqa: E402

# Made-up numbers, for the lesson only
DOCUMENT = (
    "Monitoring form for borehole GK-03, sampled on 2026-10-12. "
    "Sample W1 has pH 7.1 and DO 6.2 mg/L. "
    "Sample W2 has turbidity 12 NTU and pH 6.4. "
    "The sampler noted light rain."
)

msg = ClaudeVi().create(messages=[{"role": "user", "content": [
    {"type": "document", "title": "Form GK-03", "context": "Internal form, numbers made up for the lesson",
     "source": {"type": "text", "media_type": "text/plain", "data": DOCUMENT},
     "citations": {"enabled": True}},
    {"type": "text", "text": "Which sample has a pH below 7? Cite a source for each number."},
]}])

for block in msg.content:
    if block.type != "text":
        continue
    print(f"TEXT  {block.text!r}")
    for c in block.citations or []:
        match = DOCUMENT[c.start_char_index:c.end_char_index] == c.cited_text
        print(f"  └─ {c.type} document {c.document_index} characters {c.start_char_index}–{c.end_char_index} "
              f"{'match' if match else 'NO MATCH'}: {c.cited_text!r}")

print("\n`title` and `context` are sent to Claude but are never cited.")
