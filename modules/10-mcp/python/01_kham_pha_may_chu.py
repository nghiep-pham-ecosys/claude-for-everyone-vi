"""Module 10 — kết nối tới một MCP server và xem nó cung cấp gì.

Client khởi động may_chu_ptn.py như một process con (transport stdio), rồi hỏi danh sách tool, resource và prompt.
Không gọi Claude, không cần API key, không cần mạng.

Chạy:  uv run python modules/10-mcp/python/01_kham_pha_may_chu.py
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cau_noi import tham_so_stdio  # noqa: E402
from mcp import Client  # noqa: E402


async def main() -> None:
    async with Client(tham_so_stdio(), read_timeout_seconds=30) as mcp:
        print("1) Kết nối")
        info = mcp.server_info
        print(f"   server: {info.name if info else '?'} {info.version if info else ''}")
        print(f"   phiên bản giao thức đã thống nhất: {mcp.protocol_version}")
        print(f"   instructions: {mcp.instructions}")

        print("\n2) Tool: tên, mô tả, inputSchema (để Claude biết gọi thế nào), annotations (chỉ là gợi ý)")
        for t in (await mcp.list_tools()).tools:
            print(f"   - {t.name}: {t.description}")
            print(f"     inputSchema: {json.dumps(t.input_schema['properties'], ensure_ascii=False)}")
            if t.output_schema:
                print(f"     outputSchema: có ({', '.join(t.output_schema.get('properties', {}))})")
            a = t.annotations
            if a:
                print(f"     annotations: read_only={a.read_only_hint}, destructive={a.destructive_hint}")

        print("\n3) Resource: dữ liệu để đọc, xác định bằng URI")
        for r in (await mcp.list_resources()).resources:
            print(f"   - {r.uri} ({r.mime_type}): {r.description}")

        print("\n4) Prompt: mẫu câu do server đề xuất, người dùng chọn")
        for p in (await mcp.list_prompts()).prompts:
            ten_tham_so = [a.name for a in p.arguments or []]
            print(f"   - {p.name}({', '.join(ten_tham_so)}): {p.description}")


if __name__ == "__main__":
    asyncio.run(main())
