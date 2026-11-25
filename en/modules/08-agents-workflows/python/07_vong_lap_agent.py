"""Module 08: a hand-written agent loop with all the stop conditions (vong_lap_agent = agent loop).

On top of the tool loop of module 03, it adds:
  - stop when stop_reason == "end_turn"; stop when the turns run out; stop when the NEXT call could go over the
    cost cap (checked BEFORE the call, with the output cap from max_tokens, module 06 section 3);
  - stop_reason == "max_tokens" mid-loop: the text can be empty because thinking used up the cap
    (module 07 section 4) -> stop and say why;
  - append-only history: send back the assistant turn untouched, never shorten old tool_results,
    never change `system`;
  - a reminder on the last turn as a `system` message placed after the user turn that holds the tool_results,
    without editing the `system` parameter.

The mock in this script has multi_step on: each turn it calls ONE tool that has no result yet, and answers when
all have results. The mock does not read the reminder.

Run:  CLAUDE_MOCK=1 uv run python en/modules/08-agents-workflows/python/07_vong_lap_agent.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from phong_thi_nghiem import (  # noqa: E402
    ENV_TOOLS,
    GET_AQI,
    GET_TEMPERATURE,
    CostLog,
    make_client,
    output_cap_usd,
    read_handbook_tool,
    read_page,
)

from claude_vi import text_of  # noqa: E402

SYSTEM = "You are a (fictional) lab assistant. Use tools when you need data or a procedure. Answer briefly."
TOOLS = [read_handbook_tool(["03_lay_mau_nuoc", "06_an_toan"]), GET_AQI, GET_TEMPERATURE]
REGISTRY = {"doc_so_tay": read_page, **ENV_TOOLS}
LAST_TURN_REMINDER = "This is the last turn allowed. Conclude from the results you have; do not call more tools."


def run_tool(block) -> dict:
    """One tool_result. An unknown tool or a tool error -> is_error with a useful message (module 03 section 6)."""
    if block.name not in REGISTRY:
        return {"type": "tool_result", "tool_use_id": block.id, "is_error": True,
                "content": f"No tool '{block.name}'. Tools available: {', '.join(REGISTRY)}."}
    try:
        out = REGISTRY[block.name](**block.input)
    except Exception as e:  # noqa: BLE001 - every tool error must go back to Claude
        return {"type": "tool_result", "tool_use_id": block.id, "is_error": True,
                "content": f"{type(e).__name__}: {e}"}
    return {"type": "tool_result", "tool_use_id": block.id,
            "content": out if isinstance(out, str) else json.dumps(out, ensure_ascii=False)}


def run_agent(client, question: str, max_turns: int = 6, cap_usd: float = 0.01):
    """Returns (stop reason, last Message or None, CostLog)."""
    log = CostLog()
    cap_per_call = output_cap_usd(client.settings.model, client.settings.max_tokens)
    messages = [{"role": "user", "content": question}]
    msg = None
    for turn in range(1, max_turns + 1):
        if log.usd + cap_per_call > cap_usd:   # check BEFORE the call; input is unknown, so this is a lower bound
            return "cost_cap", msg, log
        if turn == max_turns and turn > 1:
            messages.append({"role": "system", "content": LAST_TURN_REMINDER})
        msg = log.add(client.create(system=SYSTEM, messages=messages, tools=TOOLS))
        calls = [f"{b.name}{b.input}" for b in msg.content if b.type == "tool_use"]
        print(f"  turn {turn}: stop_reason={msg.stop_reason} {' '.join(calls)}")
        if msg.stop_reason != "tool_use":
            return msg.stop_reason, msg, log   # end_turn, max_tokens, refusal, pause_turn...: the caller decides
        messages.append({"role": "assistant", "content": msg.content})   # untouched, thinking included
        messages.append({"role": "user", "content": [run_tool(b) for b in msg.content if b.type == "tool_use"]})
    return "out_of_turns", msg, log


client = make_client()
question = "I am taking water samples in Hanoi this afternoon: what should I watch for on safety, air and heat?"
cap_1 = output_cap_usd(client.settings.model, client.settings.max_tokens)

for name, kwargs in [("Enough turns, enough money", {}),
                     ("Cap of 2 turns", {"max_turns": 2}),
                     ("Cost cap just enough for one call", {"cap_usd": cap_1 * 1.01})]:
    print(f"\n{name}:")
    reason, msg, log = run_agent(client, question, **kwargs)
    print(f"  -> stopped because of {reason}; {log.report()}")
    if reason == "end_turn":
        print("  Answer:", text_of(msg)[:100].replace("\n", " "))
    elif reason == "max_tokens":
        print("  Cut off at max_tokens: the text may be empty; do not use it as a complete answer.")
print(f"\nOutput cap of ONE call with max_tokens={client.settings.max_tokens}: ${cap_1:.6f}."
      "\nThe real cost cap of the whole run must also add input, which grows every turn.")
