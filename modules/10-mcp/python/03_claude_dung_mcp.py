"""Module 10 — để Claude dùng tool của một MCP server: host làm cầu nối.

Messages API không tự nói chuyện với server chạy trên máy bạn (stdio). Host (chương trình của bạn) làm việc đó:
1. list_tools trên MCP server, đổi sang định nghĩa tool của Messages API;
2. gửi cho Claude; Claude trả tool_use;
3. host DUYỆT (theo luật của host, không theo annotation của server), rồi call_tool trên MCP server;
4. đổi kết quả sang tool_result, gửi lại cho Claude; lặp tới khi Claude trả lời.

Chạy:  CLAUDE_MOCK=1 uv run python modules/10-mcp/python/03_claude_dung_mcp.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cau_noi import can_duyet, sang_tool_claude, sang_tool_result, tao_claude, tham_so_stdio  # noqa: E402
from claude_vi import estimate_cost_usd, text_of  # noqa: E402
from mcp import Client  # noqa: E402

TOI_DA_LUOT = 5


async def hoi(claude, mcp, cau_hoi: str, nguoi_duyet) -> dict:
    """Vòng lặp tool như module 08, nhưng tool chạy trên MCP server. Trả câu trả lời, nhật ký các lời gọi, chi phí."""
    tools = sang_tool_claude((await mcp.list_tools()).tools)
    messages = [{"role": "user", "content": cau_hoi}]
    nhat_ky, usd, msg = [], 0.0, None
    for _ in range(TOI_DA_LUOT):
        msg = claude.create(messages=messages, tools=tools)
        usd += estimate_cost_usd(msg)
        messages.append({"role": "assistant", "content": msg.content})  # giữ nguyên block thinking (module 07)
        if msg.stop_reason != "tool_use":
            break
        ket_qua = []
        for b in msg.content:
            if b.type != "tool_use":
                continue
            if can_duyet(b.name) and not nguoi_duyet(b.name, b.input):
                nhat_ky.append((b.name, "không được duyệt"))
                ket_qua.append({"type": "tool_result", "tool_use_id": b.id, "is_error": True,
                                "content": [{"type": "text", "text": "Người dùng không duyệt lời gọi này."}]})
                continue
            kq = await mcp.call_tool(b.name, b.input)
            nhat_ky.append((b.name, "lỗi" if kq.is_error else "chạy"))
            ket_qua.append(sang_tool_result(b.id, kq))
        messages.append({"role": "user", "content": ket_qua})
    het_luot = msg is not None and msg.stop_reason == "tool_use"  # vẫn muốn gọi tool khi đã hết lượt
    return {"tra_loi": text_of(msg) if msg else "", "nhat_ky": nhat_ky, "usd": usd, "so_luot": len(messages) // 2,
            "stop_reason": msg.stop_reason if msg else None, "het_luot": het_luot}


async def main() -> None:
    claude = tao_claude()
    async with Client(tham_so_stdio(), read_timeout_seconds=30) as mcp:
        for ten, duyet in [("Người dùng TỪ CHỐI ghi nhật ký", False), ("Người dùng DUYỆT ghi nhật ký", True)]:
            print(f"{ten}:")
            kq = await hoi(claude, mcp, "Tra lịch HV-200 rồi ghi nhật ký kết quả.",
                           lambda name, args, d=duyet: d)
            for name, trang_thai in kq["nhat_ky"]:
                print(f"   {name:<12} {trang_thai}{'' if can_duyet(name) else ' (host cho chạy không cần hỏi)'}")
            print(f"   trả lời: {' '.join(kq['tra_loi'].split())[:80]}")
            print(f"   {kq['so_luot']} lượt gọi Claude, stop_reason={kq['stop_reason']}"
                  f"{' (HẾT LƯỢT trước khi xong)' if kq['het_luot'] else ''}, ước tính ${kq['usd']:.6f}\n")
    print("Annotation read_only_hint của server chỉ là gợi ý: host tự giữ danh sách tool được chạy không cần hỏi.")


if __name__ == "__main__":
    asyncio.run(main())
