"""Module 10 — một MCP server nhỏ: trợ lý phòng thí nghiệm hư cấu.

Server có đủ ba loại "primitive" phía server của MCP:
- tool:     tra_lich (chỉ đọc), ghi_nhat_ky (có tác dụng phụ)
- resource: ptn://so-tay (sổ tay thiết bị, chỉ đọc)
- prompt:   hoi_lich (mẫu câu hỏi cho người dùng chọn)

Chạy như một MCP server qua stdio (client khởi động nó như một process con):
    uv run python modules/10-mcp/python/may_chu_ptn.py --stdio

Không có --stdio thì chỉ in danh sách và thoát: CI chạy mọi script trong python/, server không được treo chờ stdin.
Dữ liệu đều bịa. Server không gọi Claude và không cần API key.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Literal, TypedDict

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

LICH = {  # lịch đặt thiết bị (hư cấu)
    "HV-200": "Sáng 26/11: nhóm A. Chiều 26/11: trống.",
    "LN-1200": "Cả ngày 26/11: nung mẫu M-17, không đặt được.",
    "QS-3": "Trống cả tuần.",
}
SO_TAY = Path(__file__).resolve().parents[2] / "06-cost" / "data" / "so_tay_thiet_bi.md"
# Server stdio chỉ nhận vài biến môi trường an toàn (HOME, PATH...) cộng những gì client truyền qua env=.
NHAT_KY = Path(os.environ.get("MODULE10_NHAT_KY") or Path(tempfile.gettempdir()) / "module10_nhat_ky.txt")
MAU = {"M-17": "Thép không gỉ, đang nung ở LN-1200.", "M-18": "Hợp kim nhôm, chờ đo độ cứng."}

server = MCPServer(
    "phong-thi-nghiem",
    version="1.0.0",
    instructions="Server của một phòng thí nghiệm hư cấu: tra lịch thiết bị, ghi nhật ký, đọc sổ tay.",
)


class LichThietBi(TypedDict):
    ma_thiet_bi: str
    lich: str


@server.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
def tra_lich(ma_thiet_bi: Literal["HV-200", "LN-1200", "QS-3"]) -> LichThietBi:
    """Tra lịch đặt trước của một thiết bị phòng thí nghiệm."""
    # Literal -> enum trong inputSchema; TypedDict -> outputSchema và structured_content
    return {"ma_thiet_bi": ma_thiet_bi, "lich": LICH[ma_thiet_bi]}


@server.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False))
def ghi_nhat_ky(noi_dung: str) -> str:
    """Thêm một dòng vào sổ nhật ký phòng thí nghiệm. CÓ tác dụng phụ: ghi file."""
    if not noi_dung.strip():
        # ToolError: lỗi đã lường trước -> client nhận is_error=True KÈM lời nhắn này. Exception khác bị coi là
        # crash: model chỉ thấy "Error executing tool ghi_nhat_ky", lời nhắn gốc nằm lại ở log của server.
        raise ToolError("noi_dung rỗng: hãy viết nội dung cần ghi")
    with NHAT_KY.open("a", encoding="utf-8") as f:
        f.write(noi_dung.strip() + "\n")
    return "Đã ghi nhật ký."


@server.tool(annotations=ToolAnnotations(read_only_hint=True))
def xem_mau(ma_mau: str) -> str:
    """Xem ghi chú của một mẫu đo theo mã (ví dụ M-17)."""
    # Cố ý KHÔNG kiểm mã: mã lạ làm KeyError, một crash. Model chỉ thấy "Error executing tool xem_mau",
    # lời nhắn gốc nằm ở log (stderr) của server. So với ghi_nhat_ky dùng ToolError (script 02).
    return MAU[ma_mau]


@server.resource("ptn://so-tay", name="so_tay", mime_type="text/markdown")
def so_tay() -> str:
    """Sổ tay thiết bị của phòng thí nghiệm (hư cấu)."""
    return SO_TAY.read_text("utf-8")


@server.prompt()
def hoi_lich(ma_thiet_bi: str) -> str:
    """Mẫu câu hỏi: lịch của một thiết bị và việc nên làm."""
    return f"Thiết bị {ma_thiet_bi} có lịch thế nào trong tuần này? Nếu trống, gợi ý giờ đặt."


if __name__ == "__main__":
    if "--stdio" in sys.argv:
        server.run()  # mặc định stdio: chỉ ghi message MCP ra stdout, log đi stderr
    else:
        print("MCP server 'phong-thi-nghiem': tool tra_lich, xem_mau, ghi_nhat_ky; resource ptn://so-tay;"
              " prompt hoi_lich.")
        print("Chạy làm server: uv run python modules/10-mcp/python/may_chu_ptn.py --stdio")
