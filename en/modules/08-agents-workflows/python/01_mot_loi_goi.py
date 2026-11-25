"""Module 08: three levels: one call, a workflow, an agent. Start from the lowest level (mot_loi_goi = one call).

The same task, done two ways:
  A. one call (the document goes in the prompt, as in RAG in module 04);
  B. a two-step workflow: extract the facts, then write the answer from the facts.
It prints the calls, tokens and cost of each way. The third level, an agent, is in script 07.

Run:  CLAUDE_MOCK=1 uv run python en/modules/08-agents-workflows/python/01_mot_loi_goi.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from phong_thi_nghiem import CostLog, make_client, read_page  # noqa: E402

from claude_vi import text_of  # noqa: E402

client = make_client()
document = read_page("01_hieu_chuan_ph")   # "Calibrating the pH meter" (in Vietnamese)
question = "How many buffer solutions does pH meter calibration need, and how soon must you calibrate again?"

# A. One call: enough for most questions when you already have the document
log_a = CostLog()
msg = log_a.add(client.ask(f"<document>\n{document}\n</document>\n\n{question}",
                           system="Answer briefly, using only the document."))
print("A. One call:", text_of(msg)[:80])
print("  ", log_a.report())

# B. A two-step workflow: the code decides the path, not Claude
log_b = CostLog()
step1 = log_b.add(client.ask(f"<document>\n{document}\n</document>\n\nList the facts related to: {question}",
                             system="List only facts that are in the document, one per line."))
step2 = log_b.add(client.ask(f"<facts>\n{text_of(step1)}\n</facts>\n\n{question}",
                             system="Answer briefly, using only the facts."))
print("\nB. Two-step workflow:", text_of(step2)[:80])
print("  ", log_b.report())

print("\nWay B makes twice as many calls. It is only worth it if you measure that it beats way A on your own task."
      "\nAn agent (Claude picks the next step) is even more expensive and harder to check: see script 07.")
