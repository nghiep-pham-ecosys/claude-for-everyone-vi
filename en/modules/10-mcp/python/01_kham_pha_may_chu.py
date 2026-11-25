"""Module 10: connect to an MCP server and see what it offers (kham_pha_may_chu = explore the server).

The client starts may_chu_ptn.py as a child process (stdio transport), then asks for the list of tools,
resources and prompts. No Claude call, no API key, no network.

Run:  uv run python en/modules/10-mcp/python/01_kham_pha_may_chu.py
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cau_noi import stdio_params  # noqa: E402
from mcp import Client  # noqa: E402


async def main() -> None:
    async with Client(stdio_params(), read_timeout_seconds=30) as mcp:
        print("1) Connection")
        info = mcp.server_info
        print(f"   server: {info.name if info else '?'} {info.version if info else ''}")
        print(f"   agreed protocol version: {mcp.protocol_version}")
        print(f"   instructions: {mcp.instructions}")

        print("\n2) Tools: name, description, inputSchema (so Claude knows how to call it), annotations (hints only)")
        for t in (await mcp.list_tools()).tools:
            print(f"   - {t.name}: {t.description}")
            print(f"     inputSchema: {json.dumps(t.input_schema['properties'], ensure_ascii=False)}")
            if t.output_schema:
                print(f"     outputSchema: yes ({', '.join(t.output_schema.get('properties', {}))})")
            a = t.annotations
            if a:
                print(f"     annotations: read_only={a.read_only_hint}, destructive={a.destructive_hint}")

        print("\n3) Resources: data to read, identified by a URI")
        for r in (await mcp.list_resources()).resources:
            print(f"   - {r.uri} ({r.mime_type}): {r.description}")

        print("\n4) Prompts: templates the server suggests and the user picks")
        for p in (await mcp.list_prompts()).prompts:
            arg_names = [a.name for a in p.arguments or []]
            print(f"   - {p.name}({', '.join(arg_names)}): {p.description}")


if __name__ == "__main__":
    asyncio.run(main())
