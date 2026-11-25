"""Module 10: a small MCP server, the assistant of a fictional lab (may_chu_ptn = lab server).

The server has all three server-side MCP "primitives":
- tool:     check_schedule (read-only), write_log (has a side effect)
- resource: lab://handbook (the equipment handbook, read-only)
- prompt:   ask_schedule (a question template for the user to pick)

Run it as an MCP server over stdio (the client starts it as a child process):
    uv run python en/modules/10-mcp/python/may_chu_ptn.py --stdio

Without --stdio it only prints a list and exits: CI runs every script in python/, so the server must not hang
waiting on stdin. All data is made up. The server does not call Claude and needs no API key.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Literal, TypedDict

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

SCHEDULE = {  # equipment bookings (fictional)
    "HV-200": "Morning of Nov 26: group A. Afternoon of Nov 26: free.",
    "LN-1200": "All day Nov 26: heating sample M-17, cannot be booked.",
    "QS-3": "Free all week.",
}
# The handbook is shared with module 06 and is written in Vietnamese.
HANDBOOK = Path(__file__).resolve().parents[4] / "modules" / "06-cost" / "data" / "so_tay_thiet_bi.md"
# A stdio server gets only a few safe environment variables (HOME, PATH...) plus what the client passes in env=.
LOG = Path(os.environ.get("MODULE10_LOG") or Path(tempfile.gettempdir()) / "module10_log.txt")
SAMPLES = {"M-17": "Stainless steel, heating in LN-1200.", "M-18": "Aluminum alloy, waiting for a hardness test."}

server = MCPServer(
    "lab",
    version="1.0.0",
    instructions="The server of a fictional lab: check equipment schedules, write the log, read the handbook.",
)


class DeviceSchedule(TypedDict):
    device_id: str
    schedule: str


@server.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
def check_schedule(device_id: Literal["HV-200", "LN-1200", "QS-3"]) -> DeviceSchedule:
    """Check the bookings of one piece of lab equipment."""
    # Literal -> enum in inputSchema; TypedDict -> outputSchema and structured_content
    return {"device_id": device_id, "schedule": SCHEDULE[device_id]}


@server.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False))
def write_log(text: str) -> str:
    """Add one line to the lab log book. HAS a side effect: it writes a file."""
    if not text.strip():
        # ToolError: an expected error -> the client gets is_error=True WITH this message. Any other exception
        # is a crash: the model only sees "Error executing tool write_log", the real message stays in the
        # server log.
        raise ToolError("text is empty: write what you want to log")
    with LOG.open("a", encoding="utf-8") as f:
        f.write(text.strip() + "\n")
    return "Logged."


@server.tool(annotations=ToolAnnotations(read_only_hint=True))
def view_sample(sample_id: str) -> str:
    """Show the notes for one test sample by its ID (for example M-17)."""
    # On purpose, the ID is NOT checked: an unknown ID raises KeyError, a crash. The model only sees
    # "Error executing tool view_sample"; the real message is in the server log (stderr).
    # Compare with write_log, which uses ToolError (script 02).
    return SAMPLES[sample_id]


@server.resource("lab://handbook", name="handbook", mime_type="text/markdown")
def handbook() -> str:
    """The equipment handbook of the lab (fictional, in Vietnamese)."""
    return HANDBOOK.read_text("utf-8")


@server.prompt()
def ask_schedule(device_id: str) -> str:
    """A question template: the schedule of one device and what to do next."""
    return f"What is the schedule of device {device_id} this week? If it is free, suggest a time to book it."


if __name__ == "__main__":
    if "--stdio" in sys.argv:
        server.run()  # stdio by default: only MCP messages go to stdout, logs go to stderr
    else:
        print("MCP server 'lab': tools check_schedule, view_sample, write_log; resource lab://handbook;"
              " prompt ask_schedule.")
        print("Run it as a server: uv run python en/modules/10-mcp/python/may_chu_ptn.py --stdio")
