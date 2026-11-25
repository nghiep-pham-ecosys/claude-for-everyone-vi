"""Module 05: one citation per field, when you cannot use structured outputs.

(truong kem trich dan = fields with citations)
Citations and output_config.format in the same request -> 400. The docs suggest: ask Claude to answer
each field on its own line as "name: value" and to cite a source for each line, then split it yourself in code.
Do not write "return only JSON": the request still runs, but it may have almost no citations.

Exercise 3 asks you to write the parser. This script only shows the prompt and how citations attach to blocks.

Run:  CLAUDE_MOCK=1 uv run python en/modules/05-structured-pdf-citations/python/05_truong_kem_trich_dan.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))

from claude_vi import ClaudeVi, ModelRuleError  # noqa: E402

DOCUMENT = "Sample W1 was taken on 2026-10-12 at 08:20. Sample W1 has pH 7.1 and DO 6.2 mg/L."
FIELDS = ["sample_code", "ph", "do_mg_l"]
doc = {"type": "document", "title": "Form W1", "citations": {"enabled": True},
       "source": {"type": "text", "media_type": "text/plain", "data": DOCUMENT}}
client = ClaudeVi()

# WRONG: citations + structured outputs -> claude_vi stops it first, the real API returns 400
try:
    client.create(messages=[{"role": "user", "content": [doc, {"type": "text", "text": "Extract the fields"}]}],
                  output_config={"format": {"type": "json_schema", "schema": {
                      "type": "object", "properties": {}, "additionalProperties": False}}})
except ModelRuleError as e:
    print("Stopped before sending:", str(e).splitlines()[1], "\n")

# RIGHT: one line per field, a source for each line
prompt = (f"Extract these fields from the document: {', '.join(FIELDS)}.\n"
          'Answer each field on its own line as "name: value", and cite a source for each line. '
          "After the colon, write only the value: no explanation, no quotes.")
print("Prompt:\n" + prompt + "\n")
msg = client.create(messages=[{"role": "user", "content": [doc, {"type": "text", "text": prompt}]}])

for b in msg.content:
    if b.type == "text":
        sources = [c.cited_text for c in b.citations or []]
        print(f"{b.text!r:60} {'<- ' + str(sources) if sources else ''}")

print("\nIn mock mode, the mock does not follow the 'name: value' format, so a parser would report missing fields."
      "\nThat is also the parser's job: the API does not promise that every field has a value and a citation.")
