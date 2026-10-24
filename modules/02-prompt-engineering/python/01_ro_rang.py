"""Module 02 — rõ ràng, trực tiếp, và nói "vì sao".

Claude giống một đồng nghiệp giỏi nhưng mới vào: không biết thói quen của bạn.
Prompt càng cụ thể (định dạng, độ dài, người đọc, lý do) thì kết quả càng sát ý.

Chạy:  CLAUDE_MOCK=1 uv run python modules/02-prompt-engineering/python/01_ro_rang.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from claude_vi import ClaudeVi, text_of  # noqa: E402

client = ClaudeVi()

mo_ho = "Tóm tắt bài báo này."

ro_rang = """Tóm tắt bài báo bên dưới cho sinh viên năm nhất ngành môi trường.

Yêu cầu:
1. Đúng 3 câu, mỗi câu dưới 25 từ.
2. Câu đầu nêu câu hỏi nghiên cứu, câu hai nêu phương pháp, câu ba nêu kết quả chính kèm con số.
3. Giải thích thuật ngữ chuyên ngành bằng lời thường, vì người đọc chưa học môn này.

<bai_bao>
Nghiên cứu đo nồng độ PM2.5 tại 12 trạm ở Hà Nội trong 2025. Trạm gần trục giao thông
có trung bình năm 48 µg/m³, cao hơn 1,6 lần so với trạm trong khu dân cư.
</bai_bao>"""

# Lý do đặt trong system giúp Claude tự suy ra các quy tắc chưa viết ra
system = (
    "Bạn viết tài liệu học tập. Câu trả lời sẽ được in trên slide, "
    "nên không dùng markdown, không mở đầu bằng câu dẫn kiểu 'Dưới đây là...'."
)

for ten, prompt in [("Mơ hồ", mo_ho), ("Rõ ràng", ro_rang)]:
    msg = client.ask(prompt, system=system)
    print(f"=== {ten} ({len(prompt)} ký tự prompt)\n{text_of(msg)}\n")

print("Ở mock mode hai câu trả lời giống nhau. Chạy thật để thấy khác biệt; điều cần học ở đây là prompt.")
