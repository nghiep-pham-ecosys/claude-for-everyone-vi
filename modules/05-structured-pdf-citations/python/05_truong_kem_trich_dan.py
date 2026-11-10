"""Module 05 — mỗi trường một trích dẫn, khi không dùng được structured outputs.

Citations và output_config.format trong cùng request -> 400. Docs gợi ý: xin Claude trả lời
mỗi trường một dòng "ten: gia_tri" và trích nguồn cho từng dòng, rồi tự tách trong code.
Đừng viết "chỉ trả JSON": request vẫn chạy nhưng có thể gần như không có trích dẫn nào.

Bài 3 yêu cầu bạn viết bộ tách. Script này chỉ cho xem prompt và cách citations gắn vào block.

Chạy:  CLAUDE_MOCK=1 uv run python modules/05-structured-pdf-citations/python/05_truong_kem_trich_dan.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from claude_vi import ClaudeVi, ModelRuleError  # noqa: E402

TAI_LIEU = "Mẫu W1 lấy ngày 12/10/2026 lúc 08:20. Mẫu W1 có pH 7.1 và DO 6.2 mg/L."
TRUONG = ["ma_mau", "ph", "do_mg_l"]
doc = {"type": "document", "title": "Phiếu W1", "citations": {"enabled": True},
       "source": {"type": "text", "media_type": "text/plain", "data": TAI_LIEU}}
client = ClaudeVi()

# SAI: citations + structured outputs -> claude_vi chặn trước, API thật trả 400
try:
    client.create(messages=[{"role": "user", "content": [doc, {"type": "text", "text": "Trích các trường"}]}],
                  output_config={"format": {"type": "json_schema", "schema": {
                      "type": "object", "properties": {}, "additionalProperties": False}}})
except ModelRuleError as e:
    print("Chặn trước khi gửi:", str(e).splitlines()[1], "\n")

# ĐÚNG: một dòng mỗi trường, trích nguồn từng dòng
prompt = (f"Trích các trường sau từ tài liệu: {', '.join(TRUONG)}.\n"
          'Trả lời mỗi trường một dòng dạng "ten: gia_tri" và trích nguồn cho từng dòng. '
          "Sau dấu hai chấm chỉ viết giá trị, không giải thích, không đặt trong ngoặc kép.")
print("Prompt:\n" + prompt + "\n")
msg = client.create(messages=[{"role": "user", "content": [doc, {"type": "text", "text": prompt}]}])

for b in msg.content:
    if b.type == "text":
        nguon = [c.cited_text for c in b.citations or []]
        print(f"{b.text!r:60} {'<- ' + str(nguon) if nguon else ''}")

print("\nỞ mock mode, mock không theo định dạng 'ten: gia_tri' nên bộ tách sẽ báo thiếu trường."
      "\nĐó cũng là việc bộ tách phải làm: API không đảm bảo trường nào cũng có giá trị và trích dẫn.")
