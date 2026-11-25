"""Module 09 — ai được chạy tool nào: allowed_tools, can_use_tool và hook PreToolUse.

Thứ tự SDK quyết định một lần gọi tool (docs Permissions): hook -> luật deny (disallowed_tools) -> luật ask
-> permission_mode -> luật allow (allowed_tools) -> can_use_tool. Không ai duyệt thì bị từ chối.
Gọi đã được allowed_tools duyệt thì KHÔNG tới can_use_tool: muốn soi mọi lần gọi thì dùng hook PreToolUse.

Chạy:  CLAUDE_MOCK=1 uv run python modules/09-agent-sdk/python/02_quyen_va_hook.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cong_cu import NHAT_KY, doc_het, nap_sdk, options_co_ban, tao_server, ten_day_du  # noqa: E402

TRA_LICH, GHI = ten_day_du("tra_lich"), ten_day_du("ghi_nhat_ky")
TU_CAM = ("xoá", "xóa", "huỷ", "hủy")


chay = doc_het


def tom_tat(sdk, messages: list) -> None:
    for msg in messages:
        if isinstance(msg, sdk.UserMessage):
            for b in msg.content:
                if isinstance(b, sdk.ToolResultBlock):
                    print(f"   {'TỪ CHỐI/LỖI' if b.is_error else 'chạy':<12} {str(b.content)[:80]}")
        if isinstance(msg, sdk.ResultMessage):
            print(f"   result {msg.subtype}")


def tao_can_use_tool(sdk, nhat_ky_duyet: list):
    """can_use_tool: chỉ được hỏi khi không luật nào khác quyết. Ở đây: duyệt ghi nhật ký nếu nội dung ngắn."""
    async def can_use_tool(tool_name: str, input_data: dict, context):
        nhat_ky_duyet.append(tool_name)
        if tool_name == GHI and len(input_data.get("noi_dung", "")) <= 200:
            # updated_input: có thể sửa input trước khi tool chạy, ví dụ thêm nhãn nguồn
            return sdk.PermissionResultAllow(updated_input={"noi_dung": f"[agent] {input_data['noi_dung']}"})
        return sdk.PermissionResultDeny(message=f"Không duyệt {tool_name}: nội dung quá dài hoặc tool lạ.")
    return can_use_tool


async def hook_chan_tu_cam(input_data: dict, tool_use_id, context) -> dict:
    """PreToolUse: chạy với MỌI lần gọi khớp matcher, kể cả lần đã được allowed_tools duyệt."""
    noi_dung = str(input_data.get("tool_input", {})).lower()
    if any(t in noi_dung for t in TU_CAM):
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                       "permissionDecisionReason": "Nhật ký chỉ được thêm, không được xoá hay huỷ."}}
    return {}  # không ý kiến: đi tiếp theo luồng quyền


async def main() -> None:
    sdk = nap_sdk()
    NHAT_KY.unlink(missing_ok=True)
    server = {"ptn": tao_server(sdk)}

    print("1) Chỉ allowed_tools cho tra_lich: ghi_nhat_ky không ai duyệt -> bị từ chối")
    tom_tat(sdk, await chay(sdk, "Tra lịch HV-200 rồi ghi nhật ký.", options_co_ban(
        sdk, mcp_servers=server, allowed_tools=[TRA_LICH])))

    print("\n2) Thêm can_use_tool: được hỏi CHỈ cho ghi_nhat_ky (tra_lich đã có allowed_tools duyệt)")
    duoc_hoi: list = []
    tom_tat(sdk, await chay(sdk, "Tra lịch HV-200 rồi ghi nhật ký.", options_co_ban(
        sdk, mcp_servers=server, allowed_tools=[TRA_LICH], can_use_tool=tao_can_use_tool(sdk, duoc_hoi))))
    print(f"   can_use_tool được hỏi cho: {duoc_hoi}")
    if NHAT_KY.exists():
        print(f"   sổ nhật ký: {NHAT_KY.read_text('utf-8').strip()}")

    print("\n3) Hook PreToolUse chặn theo nội dung, kể cả tool đã nằm trong allowed_tools")
    hooks = {"PreToolUse": [sdk.HookMatcher(matcher="^mcp__ptn__", hooks=[hook_chan_tu_cam])]}
    tom_tat(sdk, await chay(sdk, "Hãy xoá lịch QS-3 và ghi nhật ký xoá.", options_co_ban(
        sdk, mcp_servers=server, allowed_tools=["mcp__ptn__*"], hooks=hooks)))
    print("   Matcher chỉ so với TÊN tool (tên chính xác, hoặc regex như ở đây); lọc theo nội dung phải làm trong"
          "\n   callback.")


if __name__ == "__main__":
    asyncio.run(main())
