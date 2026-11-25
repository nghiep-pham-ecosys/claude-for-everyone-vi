"""Module 10 — gọi tool, đọc resource, lấy prompt từ MCP server, và đọc đúng kết quả.

Không gọi Claude: ở đây chính code của bạn gọi server. Script 03 mới để Claude chọn tool.

Chạy:  uv run python modules/10-mcp/python/02_goi_tool.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cau_noi import tham_so_stdio  # noqa: E402
from mcp import Client  # noqa: E402


def in_ket_qua(nhan: str, kq) -> None:
    chu = " ".join(" ".join(c.text for c in kq.content if getattr(c, "type", None) == "text").split())
    print(f"   {nhan:<26} is_error={kq.is_error} | text: {chu[:70]}")
    if kq.structured_content is not None:
        print(f"   {'':<26} structured_content: {kq.structured_content}")


async def main() -> None:
    async with Client(tham_so_stdio(), read_timeout_seconds=30) as mcp:
        print("1) Tool có outputSchema: kết quả có cả text (content) lẫn dữ liệu có cấu trúc (structured_content)")
        in_ket_qua("tra_lich(HV-200)", await mcp.call_tool("tra_lich", {"ma_thiet_bi": "HV-200"}))

        print("\n2) Lỗi trả về trong kết quả (is_error=True), client không ném exception: model đọc và tự sửa")
        in_ket_qua("tra_lich(XX-1)", await mcp.call_tool("tra_lich", {"ma_thiet_bi": "XX-1"}))
        in_ket_qua("ghi_nhat_ky('  ') ToolError", await mcp.call_tool("ghi_nhat_ky", {"noi_dung": "  "}))
        in_ket_qua("xem_mau(M-99) crash", await mcp.call_tool("xem_mau", {"ma_mau": "M-99"}))
        in_ket_qua("khong_co()", await mcp.call_tool("khong_co", {}))
        print("   ToolError: model đọc được lời nhắn. Exception khác (trừ MCPError, thành lỗi JSON-RPC) là crash:"
              "\n   model chỉ thấy 'Error executing tool <tên>', lời nhắn gốc nằm ở log của server."
              "\n   Tool lạ: theo spec là lỗi giao thức (JSON-RPC); SDK 2.3.0 vẫn trả is_error=True."
              "\n   Các dòng 'Tool ...' in phía trên là log của server ghi ra stderr, đúng luật stdio.")

        print("\n3) Resource: đọc theo URI; host quyết định đưa gì vào context")
        nd = (await mcp.read_resource("ptn://so-tay")).contents[0]
        dong = [d for d in nd.text.splitlines() if d.strip()]
        print(f"   {nd.uri} ({nd.mime_type}): {len(dong)} dòng, dòng đầu: {dong[0]}")

        print("\n4) Prompt: server trả các message mẫu; host đưa chúng vào hội thoại khi NGƯỜI DÙNG chọn")
        p = await mcp.get_prompt("hoi_lich", {"ma_thiet_bi": "QS-3"})
        for m in p.messages:
            print(f"   {m.role}: {m.content.text}")


if __name__ == "__main__":
    asyncio.run(main())
