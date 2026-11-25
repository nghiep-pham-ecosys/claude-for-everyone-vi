"""Module 10: call tools, read a resource, get a prompt from the MCP server, and read the results right
(goi_tool = call a tool).

No Claude call: here your own code calls the server. Only script 03 lets Claude pick the tools.

Run:  uv run python en/modules/10-mcp/python/02_goi_tool.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cau_noi import stdio_params  # noqa: E402
from mcp import Client  # noqa: E402


def show_result(label: str, res) -> None:
    text = " ".join(" ".join(c.text for c in res.content if getattr(c, "type", None) == "text").split())
    print(f"   {label:<30} is_error={res.is_error} | text: {text[:70]}")
    if res.structured_content is not None:
        print(f"   {'':<30} structured_content: {res.structured_content}")


async def main() -> None:
    async with Client(stdio_params(), read_timeout_seconds=30) as mcp:
        print("1) A tool with an outputSchema: the result has both text (content) and structured data"
              " (structured_content)")
        show_result("check_schedule(HV-200)", await mcp.call_tool("check_schedule", {"device_id": "HV-200"}))

        print("\n2) Errors come back inside the result (is_error=True); the client does not raise:"
              " the model reads them and fixes its call")
        show_result("check_schedule(XX-1)", await mcp.call_tool("check_schedule", {"device_id": "XX-1"}))
        show_result("write_log('  ') ToolError", await mcp.call_tool("write_log", {"text": "  "}))
        show_result("view_sample(M-99) crash", await mcp.call_tool("view_sample", {"sample_id": "M-99"}))
        show_result("no_such_tool()", await mcp.call_tool("no_such_tool", {}))
        print("   ToolError: the model can read the message. Any other exception (except MCPError, which becomes"
              "\n   a JSON-RPC error) is a crash: the model only sees 'Error executing tool <name>', and the real"
              "\n   message stays in the server log."
              "\n   Unknown tool: the spec says it is a protocol error (JSON-RPC); SDK 2.3.0 still returns"
              " is_error=True."
              "\n   The 'Tool ...' lines printed above are the server log on stderr, as the stdio rule says.")

        print("\n3) Resource: read it by URI; the host decides what goes into the context")
        item = (await mcp.read_resource("lab://handbook")).contents[0]
        lines = [d for d in item.text.splitlines() if d.strip()]
        # The handbook is in Vietnamese: "Sổ tay thiết bị" means "equipment handbook".
        print(f"   {item.uri} ({item.mime_type}): {len(lines)} lines, first line: {lines[0]}")

        print("\n4) Prompt: the server returns template messages; the host adds them to the conversation when the"
              " USER picks it")
        p = await mcp.get_prompt("ask_schedule", {"device_id": "QS-3"})
        for m in p.messages:
            print(f"   {m.role}: {m.content.text}")


if __name__ == "__main__":
    asyncio.run(main())
