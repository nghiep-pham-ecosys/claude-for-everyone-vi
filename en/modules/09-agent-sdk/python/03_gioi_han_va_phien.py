"""Module 09: the limits of one run (max_turns, max_budget_usd) and continuing a session (resume)
(gioi_han_va_phien = limits and sessions).

By default the SDK has NO limit on turns or cost. Set both for every agent that runs unattended.
When a limit is hit: ResultMessage has subtype error_max_turns / error_max_budget_usd, then query() raises
ResultError.

Run:  CLAUDE_MOCK=1 uv run python en/modules/09-agent-sdk/python/03_gioi_han_va_phien.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cong_cu import nap_sdk, options_co_ban, tao_server, ten_day_du  # noqa: E402


async def run_safely(sdk, prompt: str, options):
    """Run to the end; catch ResultError so you can still read ResultMessage (the SDK returns it BEFORE it
    raises the error)."""
    result = None
    try:
        async for msg in sdk.query(prompt=prompt, options=options):
            if isinstance(msg, sdk.ResultMessage):
                result = msg
    except sdk.ResultError as e:
        print(f"   ResultError: subtype={e.subtype}")
    return result


def print_result(r) -> None:
    usd = f"${r.total_cost_usd:.6f}" if r.total_cost_usd is not None else "none"
    print(f"   {r.subtype:<22} {r.num_turns} turns, {usd}, session {r.session_id[:13]}…")


async def main() -> None:
    sdk = nap_sdk()
    server = {"ptn": tao_server(sdk)}
    both_tools = [ten_day_du("tra_lich"), ten_day_du("ghi_nhat_ky")]
    task = "Check the LN-1200 schedule, then write the result to the log."

    print("1) max_turns=1: each turn with tool calls counts as one turn (one tool or many), and the final"
          "\n   answer adds one more turn")
    print_result(await run_safely(sdk, task, options_co_ban(
        sdk, mcp_servers=server, allowed_tools=both_tools, max_turns=1)))

    print("\n2) A very small max_budget_usd: stops after the first response over the cap (checked AFTER each"
          "\n   response, so it can go slightly over the cap)")
    print_result(await run_safely(sdk, task, options_co_ban(
        sdk, mcp_servers=server, allowed_tools=both_tools, max_budget_usd=0.000001)))

    print("\n3) Enough room: the run finishes; keep the session_id to ask more")
    first = await run_safely(sdk, task, options_co_ban(
        sdk, mcp_servers=server, allowed_tools=both_tools, max_turns=5, max_budget_usd=0.01))
    print_result(first)

    print("\n4) resume=session_id: ask more in the same session (the agent remembers the earlier turns)")
    second = await run_safely(sdk, "Sum up what you just did in one sentence.", options_co_ban(
        sdk, resume=first.session_id, max_turns=2))
    print_result(second)
    print(f"   same session: {second.session_id == first.session_id} (to branch off to a new id:"
          " fork_session=True)")
    print("   total_cost_usd of a resumed session ALREADY includes the earlier cost: do not add the two results"
          f"\n   (wrong sum: ${first.total_cost_usd + second.total_cost_usd:.6f}; right: ${second.total_cost_usd:.6f}).")


if __name__ == "__main__":
    asyncio.run(main())
