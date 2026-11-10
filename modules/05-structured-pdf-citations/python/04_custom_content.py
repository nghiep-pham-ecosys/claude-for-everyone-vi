"""Module 05 — custom content document: tự chọn đơn vị trích dẫn.

Văn bản thuần và PDF bị API cắt theo câu. Với danh sách gạch đầu dòng, bản ghi, nhật ký máy...
cắt theo câu có thể ra mảnh vô nghĩa. Custom content giữ nguyên từng block bạn đưa vào:
mỗi block là một đơn vị trích dẫn, vị trí trả về là chỉ số block (từ 0, end không tính).

Chạy:  CLAUDE_MOCK=1 uv run python modules/05-structured-pdf-citations/python/04_custom_content.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from claude_vi import ClaudeVi  # noqa: E402

NHAT_KY = [  # nhật ký máy đo, số liệu bịa
    "08:00 Hiệu chuẩn máy đo pH bằng dung dịch chuẩn 4.01 và 7.00",
    "08:20 W1: pH 7.1, nhiệt độ 26.5 °C",
    "08:35 W2: pH 6.4, nhiệt độ 27.0 °C",
    "Kết thúc ca đo, cất máy",
]

msg = ClaudeVi().create(messages=[{"role": "user", "content": [
    {"type": "document", "title": "Nhật ký máy đo 12/10", "citations": {"enabled": True},
     "source": {"type": "content", "content": [{"type": "text", "text": d} for d in NHAT_KY]}},
    {"type": "text", "text": "Liệt kê các kết quả đo pH, trích nguồn cho mỗi kết quả."},
]}])

for block in msg.content:
    for c in (block.citations or []) if block.type == "text" else []:
        dong = NHAT_KY[c.start_block_index:c.end_block_index]
        print(f"{block.text!r}\n  └─ khối {c.start_block_index}–{c.end_block_index}: {dong}")

print("\nRAG: muốn trích được từng câu trong một đoạn thì mỗi đoạn là một document văn bản thuần;"
      "\nmuốn trích nguyên đoạn thì đưa các đoạn vào một custom content document.")
