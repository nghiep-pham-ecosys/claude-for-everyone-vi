"""Module 08: evaluator-optimizer: one turn writes, one turn grades, the next turn fixes it from the feedback.
Always cap the number of rounds (danh_gia_sua = evaluate and fix).

The grading turn uses structured outputs: {"passed": bool, "feedback": str}, with the criteria spelled out in
system. In mock mode a boolean is always false, so the draft never "passes": the script runs up to MAX_ROUNDS.
That is what you need to see: without a cap this loop runs forever and multiplies the calls.

Run:  CLAUDE_MOCK=1 uv run python en/modules/08-agents-workflows/python/06_danh_gia_sua.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from phong_thi_nghiem import CostLog, make_client, read_page  # noqa: E402

from claude_vi import text_of  # noqa: E402

MAX_ROUNDS = 3
CRITERIA = ("Criteria: (1) all three buffer solutions and the order to use them; (2) the valid slope range; "
            "(3) no more than 5 sentences; (4) no information beyond the document.")
SCHEMA = {"type": "object", "properties": {"passed": {"type": "boolean"}, "feedback": {"type": "string"}},
          "required": ["passed", "feedback"], "additionalProperties": False}

client = make_client()
log = CostLog()
document = read_page("01_hieu_chuan_ph")
task = "Write a short guide for a beginner on how to calibrate the pH meter."

draft = text_of(log.add(client.ask(f"<document>\n{document}\n</document>\n\n{task}")))
passed = False
for rnd in range(1, MAX_ROUNDS + 1):
    grade = log.add(client.ask(f"<document>\n{document}\n</document>\n<draft>\n{draft}\n</draft>",
                               system="Grade the draft against the criteria. " + CRITERIA,
                               output_config={"format": {"type": "json_schema", "schema": SCHEMA}}))
    review = json.loads(text_of(grade)) if grade.stop_reason == "end_turn" else {"passed": False, "feedback": ""}
    print(f"Round {rnd}: passed={review['passed']}, feedback: {review['feedback'][:60]}")
    if review["passed"]:
        passed = True
        break
    if rnd == MAX_ROUNDS:
        break   # do not fix again: nobody would grade the last fix
    draft = text_of(log.add(client.ask(
        f"<document>\n{document}\n</document>\n<draft>\n{draft}\n</draft>\n"
        f"<feedback>\n{review['feedback']}\n</feedback>\n\nFix the draft based on the feedback. {CRITERIA}")))

print("\nResult:", "PASSED" if passed else f"not passed after {MAX_ROUNDS} rounds -> use the last draft, "
      "flag it for a person to review")
print("Whole run:", log.report())
