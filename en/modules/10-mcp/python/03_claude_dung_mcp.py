"""Module 10: let Claude use the tools of an MCP server, with the host as the bridge
(claude_dung_mcp = Claude uses MCP).

The Messages API does not talk to a server running on your machine (stdio) by itself. The host (your program)
does it:
1. list_tools on the MCP server, and turn them into Messages API tool definitions;
2. send them to Claude; Claude returns tool_use;
3. the host APPROVES the call (by the host's rules, not the server's annotations), then call_tool on the server;
4. turn the result into a tool_result and send it back to Claude; loop until Claude answers.

Run:  CLAUDE_MOCK=1 uv run python en/modules/10-mcp/python/03_claude_dung_mcp.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cau_noi import make_claude, needs_approval, stdio_params, to_claude_tools, to_tool_result  # noqa: E402
from claude_vi import estimate_cost_usd, text_of  # noqa: E402
from mcp import Client  # noqa: E402

MAX_TURNS = 5


async def ask(claude, mcp, question: str, approver) -> dict:
    """The tool loop of module 08, but the tools run on an MCP server. Returns the answer, the call log, the cost."""
    tools = to_claude_tools((await mcp.list_tools()).tools)
    messages = [{"role": "user", "content": question}]
    log, usd, msg = [], 0.0, None
    for _ in range(MAX_TURNS):
        msg = claude.create(messages=messages, tools=tools)
        usd += estimate_cost_usd(msg)
        messages.append({"role": "assistant", "content": msg.content})  # keep the thinking blocks as is (07)
        if msg.stop_reason != "tool_use":
            break
        results = []
        for b in msg.content:
            if b.type != "tool_use":
                continue
            if needs_approval(b.name) and not approver(b.name, b.input):
                log.append((b.name, "not approved"))
                results.append({"type": "tool_result", "tool_use_id": b.id, "is_error": True,
                                "content": [{"type": "text", "text": "The user did not approve this call."}]})
                continue
            res = await mcp.call_tool(b.name, b.input)
            log.append((b.name, "error" if res.is_error else "ran"))
            results.append(to_tool_result(b.id, res))
        messages.append({"role": "user", "content": results})
    out_of_turns = msg is not None and msg.stop_reason == "tool_use"  # still wants a tool after the last turn
    return {"answer": text_of(msg) if msg else "", "log": log, "usd": usd, "turns": len(messages) // 2,
            "stop_reason": msg.stop_reason if msg else None, "out_of_turns": out_of_turns}


async def main() -> None:
    claude = make_claude()
    async with Client(stdio_params(), read_timeout_seconds=30) as mcp:
        for title, approve in [("The user REFUSES the log write", False), ("The user APPROVES the log write", True)]:
            print(f"{title}:")
            res = await ask(claude, mcp, "Check the schedule of HV-200, then write the result to the log.",
                            lambda name, args, d=approve: d)
            for name, status in res["log"]:
                print(f"   {name:<14} {status}{'' if needs_approval(name) else ' (the host runs it without asking)'}")
            print(f"   answer: {' '.join(res['answer'].split())[:80]}")
            print(f"   {res['turns']} Claude calls, stop_reason={res['stop_reason']}"
                  f"{' (OUT OF TURNS before finishing)' if res['out_of_turns'] else ''},"
                  f" estimate ${res['usd']:.6f}\n")
    print("The server's read_only_hint annotation is only a hint: the host keeps its own list of tools"
          " that run without asking.")


if __name__ == "__main__":
    asyncio.run(main())
