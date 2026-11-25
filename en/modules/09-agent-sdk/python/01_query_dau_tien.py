"""Module 09: the first agent run with query() (query_dau_tien = first query). Read the stream to ResultMessage.

In module 08 you wrote the loop yourself: send a request, read stop_reason, run the tool, send tool_result,
count the turns, add up the cost. The Agent SDK runs that loop for you. You only read the messages it returns.

Run:  CLAUDE_MOCK=1 uv run python en/modules/09-agent-sdk/python/01_query_dau_tien.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cong_cu import doc_het, nap_sdk, options_co_ban, tao_server, ten_day_du, text_cua  # noqa: E402

# Read the WHOLE stream (docs: do not break at ResultMessage, some system messages can come after it),
# and catch ResultError
run = doc_het


def print_stream(sdk, messages: list) -> None:
    for msg in messages:
        if isinstance(msg, sdk.SystemMessage) and msg.subtype == "init":
            print(f"   init       session {msg.data['session_id'][:13]}…, model {msg.data['model']},"
                  f" tools: {msg.data['tools']}")
        elif isinstance(msg, sdk.AssistantMessage):
            for b in msg.content:
                if isinstance(b, sdk.ToolUseBlock):
                    print(f"   assistant  calls {b.name}({b.input})")
            if text_cua(msg):
                print(f"   assistant  {text_cua(msg)[:70]}")
        elif isinstance(msg, sdk.UserMessage):
            for b in msg.content:
                if isinstance(b, sdk.ToolResultBlock):
                    print(f"   user       tool_result{' (ERROR)' if b.is_error else ''}: {str(b.content)[:60]}")
        elif isinstance(msg, sdk.ResultMessage):
            usd = f"${msg.total_cost_usd:.6f}" if msg.total_cost_usd is not None else "none"
            print(f"   result     {msg.subtype}, {msg.num_turns} turns, estimated {usd}")


async def main() -> None:
    sdk = nap_sdk()

    print("1) No tools: one turn, one answer")
    print_stream(sdk, await run(sdk, "Hello, what can you do?", options_co_ban(sdk)))

    print("\n2) A custom tool (read only), pre-approved with allowed_tools: the SDK runs the loop itself")
    options = options_co_ban(sdk, mcp_servers={"ptn": tao_server(sdk)},
                             allowed_tools=[ten_day_du("tra_lich")],
                             disallowed_tools=[ten_day_du("ghi_nhat_ky")])  # no writing in this lesson
    messages = await run(sdk, "Is the HV-200 free this afternoon?", options)
    print_stream(sdk, messages)
    result = messages[-1] if isinstance(messages[-1], sdk.ResultMessage) else None
    if result is not None and result.subtype == "success":
        print(f"\n   The final answer is in ResultMessage.result: {result.result[:70]}")
    print("   total_cost_usd is a client-side estimate, not a bill (docs Cost tracking).")


if __name__ == "__main__":
    asyncio.run(main())
