"""Module 09 — lần chạy agent đầu tiên với query(): đọc luồng message từ đầu tới ResultMessage.

Module 08 tự viết vòng lặp: gửi request, đọc stop_reason, chạy tool, gửi tool_result, đếm lượt, cộng chi phí.
Agent SDK làm vòng lặp đó cho bạn. Bạn chỉ đọc các message nó trả ra.

Chạy:  CLAUDE_MOCK=1 uv run python modules/09-agent-sdk/python/01_query_dau_tien.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cong_cu import doc_het, nap_sdk, options_co_ban, tao_server, ten_day_du, text_cua  # noqa: E402

# Đọc HẾT luồng (docs: đừng break ở ResultMessage, vài message hệ thống có thể tới sau), bắt ResultError
chay = doc_het


def in_luong(sdk, messages: list) -> None:
    for msg in messages:
        if isinstance(msg, sdk.SystemMessage) and msg.subtype == "init":
            print(f"   init       session {msg.data['session_id'][:13]}…, model {msg.data['model']},"
                  f" tool: {msg.data['tools']}")
        elif isinstance(msg, sdk.AssistantMessage):
            for b in msg.content:
                if isinstance(b, sdk.ToolUseBlock):
                    print(f"   assistant  gọi {b.name}({b.input})")
            if text_cua(msg):
                print(f"   assistant  {text_cua(msg)[:70]}")
        elif isinstance(msg, sdk.UserMessage):
            for b in msg.content:
                if isinstance(b, sdk.ToolResultBlock):
                    print(f"   user       tool_result{' (LỖI)' if b.is_error else ''}: {str(b.content)[:60]}")
        elif isinstance(msg, sdk.ResultMessage):
            usd = f"${msg.total_cost_usd:.6f}" if msg.total_cost_usd is not None else "không có"
            print(f"   result     {msg.subtype}, {msg.num_turns} lượt, ước tính {usd}")


async def main() -> None:
    sdk = nap_sdk()

    print("1) Không tool: một lượt, một câu trả lời")
    in_luong(sdk, await chay(sdk, "Chào bạn, bạn làm được gì?", options_co_ban(sdk)))

    print("\n2) Có tool tự viết (chỉ đọc), đã duyệt trước bằng allowed_tools: SDK tự chạy vòng lặp")
    options = options_co_ban(sdk, mcp_servers={"ptn": tao_server(sdk)},
                             allowed_tools=[ten_day_du("tra_lich")],
                             disallowed_tools=[ten_day_du("ghi_nhat_ky")])  # bài này không cho ghi
    messages = await chay(sdk, "Chiều nay máy HV-200 còn trống không?", options)
    in_luong(sdk, messages)
    ket_qua = messages[-1] if isinstance(messages[-1], sdk.ResultMessage) else None
    if ket_qua is not None and ket_qua.subtype == "success":
        print(f"\n   Câu trả lời cuối nằm ở ResultMessage.result: {ket_qua.result[:70]}")
    print("   total_cost_usd là ước tính phía client, không phải hoá đơn (docs Cost tracking).")


if __name__ == "__main__":
    asyncio.run(main())
