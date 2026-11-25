"""Shared parts for the module 09 scripts: the SDK (mock or real) and the custom tools of a lab assistant.

cong_cu = tools. The tool names stay in Vietnamese, as in the exercises and the quiz:
tra_lich = check the schedule, ghi_nhat_ky = write to the log, ma_thiet_bi = device code,
noi_dung = content, ptn = lab.

All the data is made up. Run directly, this file does not call Claude.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "shared" / "py"))

from claude_vi import Settings  # noqa: E402
from claude_vi.agent_sdk import nap_sdk  # noqa: E402

LICH = {  # equipment bookings (fictional)
    "HV-200": "Morning of 26 Nov: group A. Afternoon of 26 Nov: free.",
    "LN-1200": "All day 26 Nov: firing sample M-17, cannot be booked.",
    "QS-3": "Free all week.",
}
NHAT_KY = Path(tempfile.gettempdir()) / "module09_lab_log_en.txt"
SERVER = "ptn"  # the key in mcp_servers -> the full tool name is mcp__ptn__<tool>


def ten_day_du(tool: str) -> str:
    """The full tool name (ten_day_du = full name)."""
    return f"mcp__{SERVER}__{tool}"


def tao_server(sdk: ModuleType) -> dict[str, Any]:
    """An in-process MCP server with two tools: one is read only, one has a side effect."""

    # JSON Schema form (not the simple form {"ma_thiet_bi": str}), because we need an enum (docs Custom tools)
    @sdk.tool("tra_lich", "Check the bookings of one lab device.", {
        "type": "object",
        "properties": {"ma_thiet_bi": {"type": "string", "enum": list(LICH), "description": "Device code"}},
        "required": ["ma_thiet_bi"],
    })
    async def tra_lich(args: dict[str, Any]) -> dict[str, Any]:
        code = args["ma_thiet_bi"].strip().upper()
        if code not in LICH:
            # Defense: the SDK already stops a code outside the enum before it calls the handler ("Input
            # validation error"). This branch runs only if the schema or the bookings change at run time. The
            # message still says what is wrong and which codes are valid (module 08).
            return {"content": [{"type": "text", "text": f"No device '{code}'. Valid codes: {', '.join(LICH)}"}],
                    "is_error": True}
        return {"content": [{"type": "text", "text": f"{code}: {LICH[code]}"}]}

    @sdk.tool("ghi_nhat_ky", "Write one line to the lab log book. HAS a side effect.", {"noi_dung": str})
    async def ghi_nhat_ky(args: dict[str, Any]) -> dict[str, Any]:
        with NHAT_KY.open("a", encoding="utf-8") as f:
            f.write(args["noi_dung"] + "\n")
        return {"content": [{"type": "text", "text": "Written to the log."}]}

    return sdk.create_sdk_mcp_server(name="phong-thi-nghiem", version="1.0.0", tools=[tra_lich, ghi_nhat_ky])


def options_co_ban(sdk: ModuleType, settings: Settings | None = None, **extra: Any) -> Any:
    """Shared options (options_co_ban = basic options): no built-in tools, no settings or CLAUDE.md from your
    machine, the model from config, and caps."""
    s = settings or Settings.from_env()
    base = {
        "model": s.model,
        "system_prompt": "You are a lab assistant. Answer briefly, in English.",
        "tools": [],              # turn off every built-in tool (Read, Bash...): this lesson uses custom tools only
        "setting_sources": [],    # do not load the settings and CLAUDE.md of your machine into the agent
        "max_turns": 5,           # by default the SDK has no turn limit
        "max_budget_usd": 0.01,   # ... and no cost limit (a client-side estimate, it can go slightly over)
    }
    return sdk.ClaudeAgentOptions(**{**base, **extra})


async def doc_het(sdk: ModuleType, prompt: str, options: Any) -> list[Any]:
    """Read the WHOLE message stream of one query() (doc_het = read to the end). An error result (a cap hit, a
    failed last request...) makes the SDK raise ResultError AFTER it has returned the ResultMessage: catch the
    error here so you still keep the whole stream."""
    out: list[Any] = []
    try:
        async for msg in sdk.query(prompt=prompt, options=options):
            out.append(msg)
    except sdk.ResultError as e:
        print(f"   (ResultError: {e.subtype})")
    return out


def text_cua(msg: Any) -> str:
    """Join every TextBlock of an AssistantMessage (text_cua = text of), skip ThinkingBlock/ToolUseBlock."""
    return "".join(getattr(b, "text", "") for b in msg.content if type(b).__name__ == "TextBlock")


if __name__ == "__main__":
    sdk = nap_sdk()
    print(f"SDK: {sdk.__name__}; tools: {[ten_day_du(t) for t in ('tra_lich', 'ghi_nhat_ky')]}")
