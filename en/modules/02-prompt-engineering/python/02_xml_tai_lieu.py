"""Module 02: long documents: XML tags, documents on top, the question at the end (tai_lieu = documents).

When a prompt mixes instructions, data and a question, XML tags help Claude tell which part is which.
With long documents, putting the documents FIRST and the question LAST gives better results.

Run:  CLAUDE_MOCK=1 uv run python en/modules/02-prompt-engineering/python/02_xml_tai_lieu.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))

from claude_vi import ClaudeVi, text_of  # noqa: E402

documents = [
    ("report_q1.txt", "Q1: 12,400 m³ of wastewater treated; 96% of samples met the column A standard."),
    ("report_q2.txt", "Q2: 13,100 m³ of wastewater treated; 91% of samples met the column A standard, due to a pump failure."),
]

block = "\n".join(
    f'  <document index="{i}">\n    <source>{source}</source>\n'
    f"    <document_content>\n{content}\n    </document_content>\n  </document>"
    for i, (source, content) in enumerate(documents, 1)
)
prompt = f"""<documents>
{block}
</documents>

<instructions>
Use only the information in <documents>. If the documents are not enough to answer, say so clearly.
Cite sources by the file name in <source>.
</instructions>

Question: How did the share of samples that met the standard change between the two quarters, and why?"""

print(prompt, "\n")
msg = ClaudeVi().ask(prompt)
print("Answer:", text_of(msg))
