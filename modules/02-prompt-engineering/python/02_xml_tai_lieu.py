"""Module 02 — tài liệu dài: XML tag, tài liệu ở trên, câu hỏi ở cuối.

Khi prompt trộn hướng dẫn, dữ liệu và câu hỏi, thẻ XML giúp Claude biết phần nào là gì.
Với tài liệu dài, đặt tài liệu LÊN ĐẦU và câu hỏi XUỐNG CUỐI cho kết quả tốt hơn.

Chạy:  CLAUDE_MOCK=1 uv run python modules/02-prompt-engineering/python/02_xml_tai_lieu.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from claude_vi import ClaudeVi, text_of  # noqa: E402

tai_lieu = [
    ("bao_cao_quy1.txt", "Quý 1: lượng nước thải xử lý 12.400 m³, đạt chuẩn cột A 96% số mẫu."),
    ("bao_cao_quy2.txt", "Quý 2: lượng nước thải xử lý 13.100 m³, đạt chuẩn cột A 91% số mẫu do sự cố bơm."),
]

khoi = "\n".join(
    f'  <document index="{i}">\n    <source>{nguon}</source>\n'
    f"    <document_content>\n{noi_dung}\n    </document_content>\n  </document>"
    for i, (nguon, noi_dung) in enumerate(tai_lieu, 1)
)
prompt = f"""<documents>
{khoi}
</documents>

<instructions>
Chỉ dùng thông tin trong <documents>. Nếu tài liệu không đủ để trả lời, nói rõ là không đủ.
Trích nguồn bằng tên file trong <source>.
</instructions>

Câu hỏi: Tỷ lệ mẫu đạt chuẩn thay đổi thế nào giữa hai quý, và vì sao?"""

print(prompt, "\n")
msg = ClaudeVi().ask(prompt)
print("Trả lời:", text_of(msg))
