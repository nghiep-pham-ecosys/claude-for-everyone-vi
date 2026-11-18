"""Module 08 — evaluator-optimizer: một lượt viết, một lượt chấm, lượt sau sửa theo nhận xét. Luôn có trần số vòng.

Lượt chấm dùng structured outputs: {"dat": bool, "nhan_xet": str}, với tiêu chí viết rõ trong system.
Ở mock mode boolean luôn là false, nên bản nháp không bao giờ "đạt": script chạy tới trần TOI_DA_VONG.
Đó là điều cần thấy: thiếu trần thì vòng này chạy mãi và nhân số lời gọi.

Chạy:  CLAUDE_MOCK=1 uv run python modules/08-agents-workflows/python/06_danh_gia_sua.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from phong_thi_nghiem import SoChiPhi, doc_trang, tao_client  # noqa: E402

from claude_vi import text_of  # noqa: E402

TOI_DA_VONG = 3
TIEU_CHI = ("Tiêu chí: (1) đủ ba dung dịch đệm và thứ tự dùng; (2) có khoảng độ dốc hợp lệ; "
            "(3) không quá 5 câu; (4) không thêm thông tin ngoài tài liệu.")
SCHEMA = {"type": "object", "properties": {"dat": {"type": "boolean"}, "nhan_xet": {"type": "string"}},
          "required": ["dat", "nhan_xet"], "additionalProperties": False}

client = tao_client()
so = SoChiPhi()
tai_lieu = doc_trang("01_hieu_chuan_ph")
viec = "Viết hướng dẫn ngắn cho người mới về cách hiệu chuẩn máy đo pH."

ban_nhap = text_of(so.ghi(client.ask(f"<tai_lieu>\n{tai_lieu}\n</tai_lieu>\n\n{viec}")))
dat = False
for vong in range(1, TOI_DA_VONG + 1):
    cham = so.ghi(client.ask(f"<tai_lieu>\n{tai_lieu}\n</tai_lieu>\n<ban_nhap>\n{ban_nhap}\n</ban_nhap>",
                             system="Chấm bản nháp theo tiêu chí. " + TIEU_CHI,
                             output_config={"format": {"type": "json_schema", "schema": SCHEMA}}))
    danh_gia = json.loads(text_of(cham)) if cham.stop_reason == "end_turn" else {"dat": False, "nhan_xet": ""}
    print(f"Vòng {vong}: dat={danh_gia['dat']}, nhận xét: {danh_gia['nhan_xet'][:60]}")
    if danh_gia["dat"]:
        dat = True
        break
    if vong == TOI_DA_VONG:
        break   # không sửa nữa: bản sửa cuối sẽ không ai chấm
    ban_nhap = text_of(so.ghi(client.ask(
        f"<tai_lieu>\n{tai_lieu}\n</tai_lieu>\n<ban_nhap>\n{ban_nhap}\n</ban_nhap>\n"
        f"<nhan_xet>\n{danh_gia['nhan_xet']}\n</nhan_xet>\n\nSửa bản nháp theo nhận xét. {TIEU_CHI}")))

print("\nKết quả:", "ĐẠT" if dat else f"chưa đạt sau {TOI_DA_VONG} vòng -> dùng bản cuối, gắn cờ cần người xem")
print("Cả lần chạy:", so.bao_cao())
