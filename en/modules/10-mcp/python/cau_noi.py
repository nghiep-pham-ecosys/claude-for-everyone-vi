"""Shared code for the module 10 scripts: open a connection to the MCP server and bridge MCP tools to Claude
(cau_noi = bridge).

This is the job of the "host" (the application that holds Claude): get the tool list from the MCP server, turn it
into Messages API tool definitions, call the MCP server again when Claude wants a tool, and decide which tools
need a human to approve them. This file does not call Claude when you run it directly.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "shared" / "py"))

from claude_vi import ClaudeVi, Settings  # noqa: E402
from claude_vi.mock import MockAnthropic  # noqa: E402
from mcp import StdioServerParameters  # noqa: E402

SERVER = Path(__file__).resolve().parent / "may_chu_ptn.py"
CLAUDE_NAME = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")  # the Messages API rule for tool names (module 03)
# A list set by the HOST: tools that may run without asking. Never taken from the server's annotations (hints only).
RUN_WITHOUT_ASKING = {"check_schedule", "view_sample"}


def make_claude(settings: Settings | None = None) -> ClaudeVi:
    """ClaudeVi for module 10. In mock mode, each turn the mock calls ONE tool that has no result yet (as in 08)."""
    s = settings or Settings.from_env()
    return ClaudeVi(settings=s, client=MockAnthropic(multi_step=True)) if s.mock else ClaudeVi(settings=s)


def stdio_params(env: dict[str, str] | None = None) -> StdioServerParameters:
    """The client starts the server as a child process and talks to it over its stdin/stdout.

    The child process does NOT inherit all your environment variables: the SDK passes only a few safe ones
    (HOME, PATH...) plus env. The host decides what the server sees (for example, no API key for a server that
    does not need one).
    """
    return StdioServerParameters(command=sys.executable, args=[str(SERVER), "--stdio"], env=env)


def to_claude_tools(tools: list[Any]) -> list[dict[str, Any]]:
    """MCP tool -> Messages API tool definition: name, description, input_schema.

    MCP calls it inputSchema (JSON) / input_schema (Python attribute); the Messages API calls it input_schema.
    """
    out = []
    for t in tools:
        if not CLAUDE_NAME.match(t.name):
            raise ValueError(f"The MCP tool name '{t.name}' is not valid for the Messages API")
        out.append({"name": t.name, "description": t.description or "", "input_schema": t.input_schema})
    return out


def to_tool_result(tool_use_id: str, result: Any) -> dict[str, Any]:
    """CallToolResult -> a tool_result block that KEEPS is_error.

    text -> text; image -> base64 image (a Messages API tool_result accepts images); any other type (audio,
    resource...) -> one text line saying it was dropped, so Claude does not think the tool returned nothing.
    No block but structured_content is set: send its JSON.
    """
    out: list[dict[str, Any]] = []
    for c in result.content:
        kind = getattr(c, "type", None)
        if kind == "text":
            out.append({"type": "text", "text": c.text})
        elif kind == "image":
            out.append({"type": "image", "source": {"type": "base64", "media_type": c.mime_type, "data": c.data}})
        else:
            out.append({"type": "text", "text": f"[the host dropped a '{kind}' block this lesson does not convert]"})
    if not out and result.structured_content is not None:
        out = [{"type": "text", "text": json.dumps(result.structured_content, ensure_ascii=False)}]
    if not out:
        out = [{"type": "text", "text": "(no content)"}]
    return {"type": "tool_result", "tool_use_id": tool_use_id, "content": out, "is_error": bool(result.is_error)}


def needs_approval(tool_name: str) -> bool:
    """True if the call must wait for a human to approve it. Server annotations are NEVER used to skip approval."""
    return tool_name not in RUN_WITHOUT_ASKING


if __name__ == "__main__":
    print(f"Server: {SERVER.name}; runs without asking: {sorted(RUN_WITHOUT_ASKING)}")
