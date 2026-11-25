"""Module 08: orchestrator-workers: Claude makes the list of subtasks, each worker does one, and one call
puts it all together (dieu_phoi = orchestrate).

The difference from script 04: Claude makes the task list at run time; it is not written in the code.
So the code must cap the length of the list (MAX_TASKS) and only allow pages that exist (enum).
Each subtask is one more call: the script prints the total calls and cost (module 06).

Run:  CLAUDE_MOCK=1 uv run python en/modules/08-agents-workflows/python/05_dieu_phoi.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from phong_thi_nghiem import CostLog, list_pages, make_client, read_page  # noqa: E402

from claude_vi import text_of  # noqa: E402

MAX_TASKS = 4
SCHEMA = {
    "type": "object",
    "properties": {"subtasks": {"type": "array", "items": {
        "type": "object",
        "properties": {"page": {"type": "string", "enum": list_pages()}, "question": {"type": "string"}},
        "required": ["page", "question"], "additionalProperties": False}}},
    "required": ["subtasks"],
    "additionalProperties": False,
}

client = make_client()
log = CostLog()
request = ("Prepare tomorrow's river water shift: how do we take the samples, store the samples "
           "and calibrate the pH meter?")

# 1. Orchestrator: make the plan
PLAN = (f"Split the request into at most {MAX_TASKS} subtasks. "
        "Each subtask reads exactly one handbook page and answers one narrow question.")
msg = log.add(client.ask(request, system=PLAN,
                         output_config={"format": {"type": "json_schema", "schema": SCHEMA}}))
if msg.stop_reason != "end_turn":
    raise SystemExit(f"Could not make a plan (stop_reason={msg.stop_reason}).")
subtasks = json.loads(text_of(msg))["subtasks"]
if len(subtasks) > MAX_TASKS:
    print(f"The plan has {len(subtasks)} tasks; only the first {MAX_TASKS} are done.")
    subtasks = subtasks[:MAX_TASKS]   # structured outputs does not promise an array length: cap it in code
print("Plan:", subtasks)

# 2. Workers: one call per task (they could run in parallel, as in script 04)
results = []
for t in subtasks:
    w = log.add(client.ask(f"<page>\n{read_page(t['page'])}\n</page>\n\n{t['question']}",
                           system="Use only the page you are given."))
    results.append(f"<result page=\"{t['page']}\">\n{text_of(w)}\n</result>")

# 3. Put it together
final = log.add(client.ask("\n".join(results) + f"\n\nFrom the results above, answer: {request}"))
print("Summary:", text_of(final)[:90])
print("Whole run:", log.report())
