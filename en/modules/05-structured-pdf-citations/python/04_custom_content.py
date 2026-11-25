"""Module 05: a custom content document: you choose the citation units.

The API cuts plain text and PDFs into sentences. For bullet lists, transcripts, machine logs...
cutting into sentences can give meaningless pieces. Custom content keeps each block you give it as it is:
each block is one citation unit, and the location returned is a block index (from 0, end excluded).

Run:  CLAUDE_MOCK=1 uv run python en/modules/05-structured-pdf-citations/python/04_custom_content.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))

from claude_vi import ClaudeVi  # noqa: E402

METER_LOG = [  # a meter log, made-up numbers
    "08:00 Calibrated the pH meter with standard solutions 4.01 and 7.00",
    "08:20 W1: pH 7.1, temperature 26.5 °C",
    "08:35 W2: pH 6.4, temperature 27.0 °C",
    "End of the measuring shift, meter put away",
]

msg = ClaudeVi().create(messages=[{"role": "user", "content": [
    {"type": "document", "title": "Meter log 2026-10-12", "citations": {"enabled": True},
     "source": {"type": "content", "content": [{"type": "text", "text": line} for line in METER_LOG]}},
    {"type": "text", "text": "List the pH results, and cite a source for each result."},
]}])

for block in msg.content:
    for c in (block.citations or []) if block.type == "text" else []:
        lines = METER_LOG[c.start_block_index:c.end_block_index]
        print(f"{block.text!r}\n  └─ blocks {c.start_block_index}–{c.end_block_index}: {lines}")

print("\nRAG: to cite single sentences inside a chunk, make each chunk a plain text document;"
      "\nto cite whole chunks, put the chunks in one custom content document.")
