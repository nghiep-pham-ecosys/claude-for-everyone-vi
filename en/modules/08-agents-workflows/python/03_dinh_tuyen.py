"""Module 08: routing: one call classifies, and code picks the handler by label (dinh_tuyen = routing).

The classification uses structured outputs with an `enum`, so the label is always in the list. The code still
keeps a fallback branch: a stop_reason other than "end_turn", broken JSON, or a new label added to the schema
with no handler written for it.

The mock does not understand the question: it picks the label whose keyword appears in the user turn, or else
the first label. That is why "other" comes first in the enum, and why the user turn holds only the question
(the classification instructions are in system).

Run:  CLAUDE_MOCK=1 uv run python en/modules/08-agents-workflows/python/03_dinh_tuyen.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from phong_thi_nghiem import ENV_TOOLS, GET_AQI, GET_TEMPERATURE, CostLog, make_client, read_page  # noqa: E402

from claude_vi import text_of  # noqa: E402

LABELS = ["other", "procedure", "data"]
SCHEMA = {"type": "object", "properties": {"label": {"type": "string", "enum": LABELS}},
          "required": ["label"], "additionalProperties": False}
SYSTEM_CLASSIFY = (
    "Classify the question of a lab user. procedure: asks how to do something, the steps, a device error code. "
    "data: asks for a current environmental reading (AQI, temperature). other: everything else."
)

client = make_client()
log = CostLog()


def procedure(question: str) -> str:
    document = read_page("01_hieu_chuan_ph") + "\n\n" + read_page("02_ma_loi_md300")
    msg = log.add(client.ask(f"<document>\n{document}\n</document>\n\n{question}",
                             system="Use only the document."))
    return text_of(msg)


def data(question: str) -> str:
    """The short tool loop of module 03, with a cap on turns."""
    tools, messages = [GET_AQI, GET_TEMPERATURE], [{"role": "user", "content": question}]
    for _ in range(4):
        msg = log.add(client.create(messages=messages, tools=tools))
        if msg.stop_reason != "tool_use":
            return text_of(msg)
        messages.append({"role": "assistant", "content": msg.content})
        messages.append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": b.id,
             "content": json.dumps(ENV_TOOLS[b.name](**b.input), ensure_ascii=False)}
            for b in msg.content if b.type == "tool_use"]})
    return "Not finished after 4 turns."


def other(question: str) -> str:
    return "This assistant only answers about measuring procedures and environmental data."   # costs no call


def fallback(question: str) -> str:
    return "Could not classify the question; passing it to the person in charge."


HANDLERS = {"procedure": procedure, "data": data, "other": other}


def route(question: str) -> tuple[str, str]:
    msg = log.add(client.ask(question, system=SYSTEM_CLASSIFY,
                             output_config={"format": {"type": "json_schema", "schema": SCHEMA}}))
    try:
        label = json.loads(text_of(msg))["label"] if msg.stop_reason == "end_turn" else None
    except (json.JSONDecodeError, KeyError):
        label = None
    handler = HANDLERS.get(label)
    return (label, handler(question)) if handler else ("fallback", fallback(question))


for q in ["Which steps does the procedure for calibrating the pH meter have?",
          "What is the AQI data in Hanoi right now?",
          "What should I eat for lunch today?"]:
    label, answer = route(q)
    print(f"{q}\n  -> {label}: {answer[:90]}")
print("\nWhole run:", log.report())
