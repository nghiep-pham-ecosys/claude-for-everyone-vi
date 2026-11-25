"""Module 09 — giới hạn một lần chạy (max_turns, max_budget_usd) và nối tiếp phiên (resume).

SDK mặc định KHÔNG giới hạn số lượt và chi phí. Đặt cả hai cho mọi agent chạy không có người canh.
Chạm giới hạn: ResultMessage có subtype error_max_turns / error_max_budget_usd, rồi query() ném ResultError.

Chạy:  CLAUDE_MOCK=1 uv run python modules/09-agent-sdk/python/03_gioi_han_va_phien.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cong_cu import nap_sdk, options_co_ban, tao_server, ten_day_du  # noqa: E402


async def chay_an_toan(sdk, prompt: str, options):
    """Chạy tới hết; bắt ResultError để vẫn đọc được ResultMessage (SDK trả nó TRƯỚC khi ném lỗi)."""
    ket_qua = None
    try:
        async for msg in sdk.query(prompt=prompt, options=options):
            if isinstance(msg, sdk.ResultMessage):
                ket_qua = msg
    except sdk.ResultError as e:
        print(f"   ResultError: subtype={e.subtype}")
    return ket_qua


def in_ket_qua(r) -> None:
    usd = f"${r.total_cost_usd:.6f}" if r.total_cost_usd is not None else "không có"
    print(f"   {r.subtype:<22} {r.num_turns} lượt, {usd}, session {r.session_id[:13]}…")


async def main() -> None:
    sdk = nap_sdk()
    server = {"ptn": tao_server(sdk)}
    hai_tool = [ten_day_du("tra_lich"), ten_day_du("ghi_nhat_ky")]
    viec = "Tra lịch LN-1200 rồi ghi nhật ký kết quả."

    print("1) max_turns=1: mỗi lượt có gọi tool tính một lượt (dù gọi một hay nhiều tool), câu trả lời cuối"
          "\n   thêm một lượt")
    in_ket_qua(await chay_an_toan(sdk, viec, options_co_ban(
        sdk, mcp_servers=server, allowed_tools=hai_tool, max_turns=1)))

    print("\n2) max_budget_usd rất nhỏ: dừng sau response đầu tiên vượt trần (kiểm SAU mỗi response, nên có thể"
          "\n   vượt trần một chút)")
    in_ket_qua(await chay_an_toan(sdk, viec, options_co_ban(
        sdk, mcp_servers=server, allowed_tools=hai_tool, max_budget_usd=0.000001)))

    print("\n3) Đủ giới hạn: chạy xong, giữ session_id để hỏi tiếp")
    dau = await chay_an_toan(sdk, viec, options_co_ban(
        sdk, mcp_servers=server, allowed_tools=hai_tool, max_turns=5, max_budget_usd=0.01))
    in_ket_qua(dau)

    print("\n4) resume=session_id: hỏi tiếp trong cùng phiên (agent nhớ lượt trước)")
    sau = await chay_an_toan(sdk, "Tóm tắt lại việc vừa làm trong một câu.", options_co_ban(
        sdk, resume=dau.session_id, max_turns=2))
    in_ket_qua(sau)
    print(f"   cùng session: {sau.session_id == dau.session_id} (muốn rẽ nhánh sang id mới: fork_session=True)")
    print("   total_cost_usd của phiên resume ĐÃ gồm chi phí lần trước: đừng cộng hai kết quả với nhau"
          f"\n   (cộng sai: ${dau.total_cost_usd + sau.total_cost_usd:.6f}; đúng: ${sau.total_cost_usd:.6f}).")


if __name__ == "__main__":
    asyncio.run(main())
