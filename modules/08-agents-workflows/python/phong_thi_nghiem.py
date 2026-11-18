"""Phần dùng chung cho các script module 08: client, tool của trợ lý phòng thí nghiệm, sổ chi phí.

Dữ liệu đều bịa: sổ tay của module 04, hai tool AQI/nhiệt độ của module 03, một trang có chỉ dẫn chèn vào.
File này không gọi Claude khi chạy trực tiếp.
"""
from __future__ import annotations

import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared" / "py"))
sys.path.insert(0, str(ROOT / "modules" / "03-tool-use" / "python"))

from claude_vi import ClaudeVi, Settings, estimate_cost_usd, load_models  # noqa: E402
from claude_vi.mock import MockAnthropic  # noqa: E402
from tools_mau import REGISTRY as TOOLS_MOI_TRUONG  # noqa: E402,F401
from tools_mau import TRA_AQI, TRA_NHIET_DO  # noqa: E402,F401

SO_TAY = ROOT / "modules" / "04-rag" / "data" / "so_tay"
DATA = Path(__file__).resolve().parents[1] / "data"
TRANG_CHEN = "99_ghi_chu_ca_dem"   # trang có câu chỉ dẫn chèn vào (bài 6)


def tao_client(settings: Settings | None = None) -> ClaudeVi:
    """ClaudeVi cho module 08. Ở mock mode bật multi_step: mỗi lượt mock gọi MỘT tool, như một agent nhiều bước.

    ClaudeVi() mặc định dựng MockAnthropic() không có multi_step, nên vòng lặp agent luôn dừng sau một vòng tool.
    Chạy thật: ClaudeVi(settings) dùng SDK thật, tham số multi_step không liên quan.
    """
    s = settings or Settings.from_env()
    return ClaudeVi(settings=s, client=MockAnthropic(multi_step=True)) if s.mock else ClaudeVi(settings=s)


def danh_sach_trang() -> list[str]:
    return sorted(p.stem for p in SO_TAY.glob("*.md"))


def doc_trang(trang: str) -> str:
    """Nội dung một trang sổ tay (module 04) hoặc trang mẫu của module 08. Tên lạ -> FileNotFoundError."""
    for thu_muc in (SO_TAY, DATA):
        path = thu_muc / f"{trang}.md"
        if path.is_file():
            return path.read_text("utf-8")
    raise FileNotFoundError(f"không có trang '{trang}'. Trang hiện có: {', '.join(danh_sach_trang())}")


def tool_doc_so_tay(trang: list[str]) -> dict:
    """Tool chỉ đọc. Danh sách trang là enum: Claude chỉ chọn được trang của nhiệm vụ này."""
    return {
        "name": "doc_so_tay",
        "description": (
            "Đọc nguyên văn một trang trong sổ tay phòng thí nghiệm (hư cấu). "
            "Dùng khi cần quy trình đo, mã lỗi thiết bị hoặc ghi chú ca trước. "
            "Chỉ đọc, không thay đổi gì. Chỉ nhận tên trang trong danh sách enum."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {"trang": {"type": "string", "enum": trang}},
            "required": ["trang"],
            "additionalProperties": False,
        },
    }


GHI_NHAT_KY = {
    "name": "ghi_nhat_ky",
    "description": (
        "Ghi MỘT dòng vào nhật ký đo của phòng thí nghiệm. Có tác dụng phụ: dòng đã ghi không xoá được. "
        "Chỉ dùng khi người dùng yêu cầu ghi nhật ký. Mỗi lần ghi cần người phụ trách duyệt."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {"noi_dung": {"type": "string", "description": "một dòng, không xuống dòng"}},
        "required": ["noi_dung"],
        "additionalProperties": False,
    },
}


def tao_nhat_ky(path: Path | None = None):
    """Hàm ghi_nhat_ky ghi vào một file tạm (không commit). Trả (hàm, đường dẫn file)."""
    path = path or Path(tempfile.mkdtemp(prefix="nhat_ky_")) / "nhat_ky.txt"

    def ghi_nhat_ky(noi_dung: str) -> dict:
        with path.open("a", encoding="utf-8") as f:
            f.write(noi_dung.replace("\n", " ") + "\n")
        return {"da_ghi": True, "file": path.name}

    return ghi_nhat_ky, path


def tran_output_usd(model: str, max_tokens: int) -> float:
    """Chi phí output tối đa của MỘT lời gọi (module 06 mục 3): max_tokens là trần cứng cho thinking + text."""
    gia = load_models()["models"].get(model, {}).get("price_per_mtok")
    return max_tokens * gia["output"] / 1_000_000 if gia else float("nan")


class SoChiPhi:
    """Ghi mọi Message của một lần chạy để tính tổng lời gọi, token và chi phí.

    Tổng chi phí = tổng estimate_cost_usd của MỌI lời gọi, không chỉ lời gọi cuối.
    Vẫn là ước tính thô: bỏ qua token cache (module 06 mục 5).
    """

    def __init__(self) -> None:
        self.msgs: list = []
        self._khoa = threading.Lock()   # script 04 ghi từ nhiều luồng

    def ghi(self, msg):
        with self._khoa:
            self.msgs.append(msg)
        return msg

    @property
    def so_loi_goi(self) -> int:
        return len(self.msgs)

    @property
    def usd(self) -> float:
        return sum(estimate_cost_usd(m) for m in self.msgs)

    def bao_cao(self) -> str:
        vao = sum(m.usage.input_tokens for m in self.msgs)
        ra = sum(m.usage.output_tokens for m in self.msgs)
        return f"{self.so_loi_goi} lời gọi, {vao} token vào, {ra} token ra, ≈ ${self.usd:.6f}"
