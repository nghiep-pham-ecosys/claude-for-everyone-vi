"""Phần dùng chung cho các script module 09: SDK (mock hoặc thật), tool tự viết của trợ lý phòng thí nghiệm.

Dữ liệu đều bịa. File này không gọi Claude khi chạy trực tiếp.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared" / "py"))

from claude_vi import Settings  # noqa: E402
from claude_vi.agent_sdk import nap_sdk  # noqa: E402

LICH = {  # lịch đặt thiết bị (hư cấu)
    "HV-200": "Sáng 26/11: nhóm A. Chiều 26/11: trống.",
    "LN-1200": "Cả ngày 26/11: nung mẫu M-17, không đặt được.",
    "QS-3": "Trống cả tuần.",
}
NHAT_KY = Path(tempfile.gettempdir()) / "module09_nhat_ky.txt"
SERVER = "ptn"  # khoá trong mcp_servers -> tên tool đầy đủ là mcp__ptn__<tool>


def ten_day_du(tool: str) -> str:
    return f"mcp__{SERVER}__{tool}"


def tao_server(sdk: ModuleType) -> dict[str, Any]:
    """Server MCP chạy trong process với hai tool: một tool chỉ đọc, một tool có tác dụng phụ."""

    # Dạng JSON Schema (không phải dạng đơn giản {"ma_thiet_bi": str}) vì cần enum (docs Custom tools)
    @sdk.tool("tra_lich", "Tra lịch đặt trước của một thiết bị phòng thí nghiệm.", {
        "type": "object",
        "properties": {"ma_thiet_bi": {"type": "string", "enum": list(LICH), "description": "Mã thiết bị"}},
        "required": ["ma_thiet_bi"],
    })
    async def tra_lich(args: dict[str, Any]) -> dict[str, Any]:
        ma = args["ma_thiet_bi"].strip().upper()
        if ma not in LICH:
            # Phòng thủ: SDK đã chặn mã ngoài enum trước khi gọi handler ("Input validation error"). Nhánh này chỉ
            # chạy khi schema đổi hoặc lịch đổi lúc chạy. Lời nhắn vẫn nói sai gì và mã nào hợp lệ (module 08).
            return {"content": [{"type": "text", "text": f"Không có thiết bị '{ma}'. Mã hợp lệ: {', '.join(LICH)}"}],
                    "is_error": True}
        return {"content": [{"type": "text", "text": f"{ma}: {LICH[ma]}"}]}

    @sdk.tool("ghi_nhat_ky", "Ghi một dòng vào sổ nhật ký phòng thí nghiệm. CÓ tác dụng phụ.", {"noi_dung": str})
    async def ghi_nhat_ky(args: dict[str, Any]) -> dict[str, Any]:
        with NHAT_KY.open("a", encoding="utf-8") as f:
            f.write(args["noi_dung"] + "\n")
        return {"content": [{"type": "text", "text": "Đã ghi nhật ký."}]}

    return sdk.create_sdk_mcp_server(name="phong-thi-nghiem", version="1.0.0", tools=[tra_lich, ghi_nhat_ky])


def options_co_ban(sdk: ModuleType, settings: Settings | None = None, **them: Any) -> Any:
    """Options dùng chung: không tool dựng sẵn, không đọc settings/CLAUDE.md của máy, model từ config, có trần."""
    s = settings or Settings.from_env()
    base = {
        "model": s.model,
        "system_prompt": "Bạn là trợ lý phòng thí nghiệm. Trả lời ngắn, bằng tiếng Việt.",
        "tools": [],              # tắt mọi tool dựng sẵn (Read, Bash...): bài này chỉ dùng tool tự viết
        "setting_sources": [],    # không nạp settings và CLAUDE.md của máy bạn vào agent
        "max_turns": 5,           # SDK mặc định không giới hạn lượt
        "max_budget_usd": 0.01,   # ... và không giới hạn chi phí (ước tính phía client, có thể vượt một chút)
    }
    return sdk.ClaudeAgentOptions(**{**base, **them})


async def doc_het(sdk: ModuleType, prompt: str, options: Any) -> list[Any]:
    """Đọc HẾT luồng message của một query(). Result lỗi (chạm trần, request cuối hỏng...) làm SDK ném ResultError
    SAU khi đã trả ResultMessage: bắt lỗi ở đây để vẫn giữ được cả luồng."""
    out: list[Any] = []
    try:
        async for msg in sdk.query(prompt=prompt, options=options):
            out.append(msg)
    except sdk.ResultError as e:
        print(f"   (ResultError: {e.subtype})")
    return out


def text_cua(msg: Any) -> str:
    """Ghép mọi TextBlock của một AssistantMessage, bỏ qua ThinkingBlock/ToolUseBlock."""
    return "".join(getattr(b, "text", "") for b in msg.content if type(b).__name__ == "TextBlock")


if __name__ == "__main__":
    sdk = nap_sdk()
    print(f"SDK: {sdk.__name__}; tool: {[ten_day_du(t) for t in ('tra_lich', 'ghi_nhat_ky')]}")
