"""Module 04: let Claude search on its own: a tool that returns search_result blocks.

Script 04 always searches first, then asks. Here Claude decides whether it needs to search, which keywords
to use, and whether to search again. The tool returns a list of search_result blocks; when nothing is found
it returns a text block that says so, instead of raising an error. tool_choice stays "auto"
(any/tool return 400 on Opus/Sonnet 5.5 and Fable 5.x).

Run:  CLAUDE_MOCK=1 uv run python en/modules/04-rag/python/05_rag_tool.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "shared" / "py"))
sys.path.insert(0, str(ROOT / "modules" / "04-rag" / "python"))

from claude_vi import ClaudeVi, text_of  # noqa: E402
from rag_mau import hop, tat_ca_doan, tim  # noqa: E402

chunks, texts = tat_ca_doan()
SEARCH_HANDBOOK = {
    "name": "search_handbook",
    "description": ("Search the internal handbook of an environmental lab: how to take and store samples, "
                    "calibration and error codes of the meters, safety, equipment management. "
                    "The handbook is in Vietnamese: search with Vietnamese keywords, or with codes such as "
                    "error codes, device codes or parameter names. Returns at most the 3 most relevant chunks."),
    "strict": True,
    "input_schema": {"type": "object",
                     "properties": {"keywords": {"type": "string", "description": "search keywords"}},
                     "required": ["keywords"], "additionalProperties": False},
}


def run_tool(keywords: str) -> list[dict]:
    found = tim(chunks, texts, keywords, k=3)
    return hop.khoi_ket_qua(found) if found else [{"type": "text", "text": "No chunk found."}]


client = ClaudeVi()
messages = [{"role": "user", "content": "How long can a turbidity sample be kept before analysis?"}]
for turn in range(1, 5):
    msg = client.create(messages=messages, tools=[SEARCH_HANDBOOK])
    messages.append({"role": "assistant", "content": msg.content})
    if msg.stop_reason != "tool_use":
        break
    results = []
    for call in (b for b in msg.content if b.type == "tool_use"):
        keywords = call.input["keywords"]
        if keywords == "[MOCK]":                   # the mock fills in the minimum value the schema allows
            keywords = "độ đục bảo quản"           # Vietnamese for "turbidity storage"
        print(f"Turn {turn}: Claude calls search_handbook({keywords!r})")
        results.append({"type": "tool_result", "tool_use_id": call.id, "content": run_tool(keywords)})
    messages.append({"role": "user", "content": results})

print("\nAnswer:", text_of(msg))
for n in hop.nguon_trich_dan(msg):
    print(f"  source {n['source']}: {n['cited_text']!r}")
