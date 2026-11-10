"""Module 07 — lịch sử append-only và prefix check.

Một block thinking chỉ hợp lệ khi mọi thứ gửi TRƯỚC nó không đổi: system, tools, và các message trước.
Sửa system giữa chừng (thêm ngày tháng, đổi chế độ...) làm block thinking của các lượt sau hỏng.
Trên Haiku/Sonnet/Opus 5.5 và Fable 5.1/5.2, tài khoản tạo từ 31/8/2026 nhận lỗi 400.

Cách đúng: giữ system cố định, thêm chỉ dẫn mới bằng một message role "system" đặt sau lượt user.

Chạy:  CLAUDE_MOCK=1 uv run python modules/07-thinking/python/05_append_only.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

import anthropic  # noqa: E402
from claude_vi import ClaudeVi, text_of  # noqa: E402

client = ClaudeVi()
SYSTEM = "Bạn là trợ giảng hoá học, trả lời ngắn."
u1 = {"role": "user", "content": "pH là gì?"}
a1 = client.create(system=SYSTEM, messages=[u1])
u2 = {"role": "user", "content": "Cho một ví dụ."}
lich_su = [u1, {"role": "assistant", "content": a1.content}, u2]

# SAI: sửa system rồi gửi lại block thinking của lượt 1
try:
    msg = client.create(system=SYSTEM + " Trả lời bằng tiếng Anh.", messages=lich_su)
    print("SAI nhưng không lỗi: tài khoản tạo trước 31/8/2026 có thể không bị 400 trên model này;"
          "\nblock lệch vẫn tới model. Người dùng code của bạn với tài khoản mới sẽ bị 400.")
except anthropic.BadRequestError as e:
    loi = (e.body or {}).get("error", {}).get("message", e.message) if isinstance(e.body, dict) else e.message
    print("SAI -> 400:", loi)

# ĐÚNG: system giữ nguyên, chỉ dẫn mới là một message system đặt ngay sau lượt user
msg = client.create(system=SYSTEM, messages=[*lich_su, {"role": "system", "content": "Từ giờ trả lời bằng tiếng Anh."}])
print("\nĐÚNG ->", text_of(msg))
print("\nMessage system giữa hội thoại không dành cho dữ liệu bên ngoài (kết quả tool, web): Claude coi nó là"
      "\nchỉ dẫn của nhà phát triển. Dữ liệu ngoài vẫn để trong tool_result.")
