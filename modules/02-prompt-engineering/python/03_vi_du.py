"""Module 02 — dạy bằng ví dụ (few-shot / multishot prompting).

Vài ví dụ tốt là cách chắc nhất để cố định định dạng và giọng văn.
Docs khuyên 3–5 ví dụ, sát với dữ liệu thật, đủ đa dạng, bọc trong <example>.

Chạy:  CLAUDE_MOCK=1 uv run python modules/02-prompt-engineering/python/03_vi_du.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from claude_vi import ClaudeVi, text_of  # noqa: E402

vi_du = [
    ("Bài giảng dễ hiểu nhưng phòng lab thiếu máy đo pH.", "co_so_vat_chat"),
    ("Thầy giải thích lại khi lớp chưa hiểu, rất kiên nhẫn.", "giang_day"),
    ("Đề thi giữa kỳ có câu ngoài nội dung đã học.", "danh_gia"),
    ("Mọi thứ ổn.", "khac"),  # ví dụ "khó": không thuộc nhóm nào rõ ràng
]
khoi_vi_du = "\n".join(
    f"<example>\n<phan_hoi>{van_ban}</phan_hoi>\n<nhom>{nhom}</nhom>\n</example>" for van_ban, nhom in vi_du
)

system = (
    "Bạn phân loại phản hồi của sinh viên vào đúng một nhóm: "
    "giang_day, danh_gia, co_so_vat_chat, khac. Chỉ trả về tên nhóm."
)
prompt = f"""<examples>
{khoi_vi_du}
</examples>

<phan_hoi>Máy chiếu phòng B2 mờ, ngồi cuối không đọc được slide.</phan_hoi>"""

print(prompt, "\n")
msg = ClaudeVi().ask(prompt, system=system)
print("Nhóm:", text_of(msg))
print("\nMuốn chắc chắn đầu ra là một trong 4 nhóm? Dùng structured outputs (script 04).")
