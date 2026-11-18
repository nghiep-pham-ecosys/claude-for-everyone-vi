"""Bài 2 — router theo nhãn enum, có nhánh dự phòng.

dinh_tuyen(client, cau_hoi, xu_ly, du_phong) -> (nhan, ket_qua)
    - MỘT lời gọi phân loại: client.ask(cau_hoi, system=SYSTEM,
      output_config={"format": {"type": "json_schema", "schema": SCHEMA}}).
      Lượt user chỉ chứa câu hỏi; chỉ dẫn phân loại nằm trong SYSTEM.
    - Đọc nhãn từ JSON (khoá "nhan"). Nhãn có trong xu_ly -> trả (nhan, xu_ly[nhan](cau_hoi)).
    - Mọi trường hợp còn lại -> ("du_phong", du_phong(cau_hoi)):
      stop_reason khác "end_turn", JSON hỏng, thiếu khoá, nhãn lạ, nhãn hợp lệ nhưng xu_ly chưa có hàm.
    - Không gọi Claude thêm lần nào: hàm xử lý tự quyết có gọi hay không.

Mock không hiểu câu hỏi: nó chọn nhãn có từ khoá trong câu hỏi, không có thì nhãn đầu ("khac").

Chấm:  CHAM=exercises uv run pytest modules/08-agents-workflows -q
"""
from __future__ import annotations

from collections.abc import Callable

from claude_vi import ClaudeVi

NHAN = ["khac", "quy_trinh", "so_lieu"]
SCHEMA = {"type": "object", "properties": {"nhan": {"type": "string", "enum": NHAN}},
          "required": ["nhan"], "additionalProperties": False}
SYSTEM = (
    "Phân loại câu hỏi của người dùng phòng thí nghiệm. quy_trinh: hỏi cách làm, các bước, mã lỗi thiết bị. "
    "so_lieu: hỏi số đo môi trường hiện tại. khac: mọi câu còn lại."
)


def dinh_tuyen(client: ClaudeVi, cau_hoi: str, xu_ly: dict[str, Callable[[str], str]],
               du_phong: Callable[[str], str]) -> tuple[str, str]:
    raise NotImplementedError("TODO: bài 2")
