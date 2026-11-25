"""Phần dùng chung cho các script module 10: mở kết nối tới MCP server và nối tool MCP với Claude.

Đây là việc của "host" (ứng dụng chứa Claude): lấy danh sách tool từ MCP server, đổi thành định nghĩa tool của
Messages API, gọi lại MCP server khi Claude muốn dùng tool, và quyết định tool nào cần người duyệt.
File này không gọi Claude khi chạy trực tiếp.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared" / "py"))

from claude_vi import ClaudeVi, Settings  # noqa: E402
from claude_vi.mock import MockAnthropic  # noqa: E402
from mcp import StdioServerParameters  # noqa: E402

MAY_CHU = Path(__file__).resolve().parent / "may_chu_ptn.py"
TEN_CLAUDE = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")  # luật tên tool của Messages API (module 03)
# Danh sách do HOST đặt: tool được chạy không cần hỏi. Không lấy từ annotation của server (chỉ là gợi ý).
CHAY_KHONG_HOI = {"tra_lich", "xem_mau"}


def tao_claude(settings: Settings | None = None) -> ClaudeVi:
    """ClaudeVi cho module 10. Ở mock mode: mỗi lượt mock gọi MỘT tool chưa có kết quả (như module 08)."""
    s = settings or Settings.from_env()
    return ClaudeVi(settings=s, client=MockAnthropic(multi_step=True)) if s.mock else ClaudeVi(settings=s)


def tham_so_stdio(env: dict[str, str] | None = None) -> StdioServerParameters:
    """Client khởi động server như một process con và nói chuyện qua stdin/stdout của nó.

    Process con KHÔNG thừa hưởng mọi biến môi trường: SDK chỉ chuyển vài biến an toàn (HOME, PATH...) cộng env.
    Host quyết định server thấy gì (ví dụ không đưa API key cho server không cần).
    """
    return StdioServerParameters(command=sys.executable, args=[str(MAY_CHU), "--stdio"], env=env)


def sang_tool_claude(tools: list[Any]) -> list[dict[str, Any]]:
    """Tool MCP -> định nghĩa tool của Messages API: name, description, input_schema.

    MCP gọi là inputSchema (JSON) / input_schema (thuộc tính Python); Messages API gọi là input_schema.
    """
    out = []
    for t in tools:
        if not TEN_CLAUDE.match(t.name):
            raise ValueError(f"Tên tool MCP '{t.name}' không hợp lệ với Messages API")
        out.append({"name": t.name, "description": t.description or "", "input_schema": t.input_schema})
    return out


def sang_tool_result(tool_use_id: str, ket_qua: Any) -> dict[str, Any]:
    """CallToolResult -> block tool_result, GIỮ is_error.

    text -> text; image -> image base64 (tool_result của Messages API nhận ảnh); loại khác (audio, resource...)
    -> một dòng text báo đã bỏ, để Claude không tưởng tool không trả gì. Không có block nào mà có
    structured_content thì gửi JSON của nó.
    """
    out: list[dict[str, Any]] = []
    for c in ket_qua.content:
        loai = getattr(c, "type", None)
        if loai == "text":
            out.append({"type": "text", "text": c.text})
        elif loai == "image":
            out.append({"type": "image", "source": {"type": "base64", "media_type": c.mime_type, "data": c.data}})
        else:
            out.append({"type": "text", "text": f"[host bỏ một block '{loai}' mà bài này chưa chuyển đổi]"})
    if not out and ket_qua.structured_content is not None:
        out = [{"type": "text", "text": json.dumps(ket_qua.structured_content, ensure_ascii=False)}]
    if not out:
        out = [{"type": "text", "text": "(không có nội dung)"}]
    return {"type": "tool_result", "tool_use_id": tool_use_id, "content": out, "is_error": bool(ket_qua.is_error)}


def can_duyet(ten_tool: str) -> bool:
    """True nếu lời gọi phải chờ người duyệt. Annotation của server KHÔNG được dùng để bỏ qua bước duyệt."""
    return ten_tool not in CHAY_KHONG_HOI


if __name__ == "__main__":
    print(f"Server: {MAY_CHU.name}; chạy không cần hỏi: {sorted(CHAY_KHONG_HOI)}")
