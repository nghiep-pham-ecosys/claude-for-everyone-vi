"""Module 08 — chạy song song: chia phần (sectioning) và bỏ phiếu (voting).

Chia phần: mỗi trang sổ tay một lời gọi chạy đồng thời, rồi code gộp kết quả.
Bỏ phiếu: cùng một câu hỏi gọi nhiều lần, lấy đa số.

Ba điều luôn làm:
  - giới hạn số lời gọi đồng thời (max_workers), để không tự gây 429;
  - bắt lỗi CÓ KIỂU ở từng nhánh: một nhánh hỏng không làm sập cả lần chạy;
  - không bọc thêm vòng retry: SDK đã tự thử lại 429 và 5xx (module 01 mục 7).
Mỗi nhánh một ClaudeVi: cách đơn giản nhất, không phụ thuộc client có dùng chung được giữa các luồng hay không.

Chạy:  CLAUDE_MOCK=1 uv run python modules/08-agents-workflows/python/04_song_song.py
"""
import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import anthropic  # noqa: E402
from phong_thi_nghiem import SoChiPhi, doc_trang, tao_client  # noqa: E402

from claude_vi import text_of  # noqa: E402

so = SoChiPhi()


def tom_tat_trang(trang: str) -> str:
    """Một nhánh. Lỗi trả về dạng chuỗi có kiểu, không ném ra ngoài."""
    try:
        noi_dung = doc_trang(trang)
        msg = so.ghi(tao_client().ask(f"<trang>\n{noi_dung}\n</trang>\n\nTóm tắt trang này trong một câu."))
        return text_of(msg)
    except (anthropic.APIError, OSError) as e:
        return f"LỖI {type(e).__name__}: {e}"


trang = ["01_hieu_chuan_ph", "03_lay_mau_nuoc", "05_do_do_quang", "08_khong_co"]   # trang cuối cố ý không có
with ThreadPoolExecutor(max_workers=2) as pool:
    ket_qua = list(pool.map(tom_tat_trang, trang))   # map giữ đúng thứ tự trang
print("Chia phần:")
for t, kq in zip(trang, ket_qua):
    print(f"  {t}: {kq[:80]}")
loi = sum(kq.startswith("LỖI") for kq in ket_qua)
print(f"  Gộp: {len(trang) - loi}/{len(trang)} nhánh thành công; nhánh lỗi được báo, không làm sập lần chạy.")

SCHEMA = {"type": "object", "properties": {"ket_luan": {"type": "string", "enum": ["can_do_lai", "khong_can"]}},
          "required": ["ket_luan"], "additionalProperties": False}
cau_hoi = doc_trang("02_ma_loi_md300") + "\n\nMẫu đo khi máy báo E-31 có cần đo lại không?"


def mot_phieu(_: int) -> str | None:
    try:
        msg = so.ghi(tao_client().ask(cau_hoi, output_config={"format": {"type": "json_schema", "schema": SCHEMA}}))
        return json.loads(text_of(msg))["ket_luan"] if msg.stop_reason == "end_turn" else None
    except anthropic.APIError:
        return None


with ThreadPoolExecutor(max_workers=3) as pool:
    phieu = [p for p in pool.map(mot_phieu, range(3)) if p]
if not phieu:
    raise SystemExit("Không phiếu nào hợp lệ: không kết luận.")
nhan, so_phieu = Counter(phieu).most_common(1)[0]
print(f"\nBỏ phiếu: {phieu} -> {nhan} ({so_phieu}/{len(phieu)})")
print("Mock luôn trả cùng một nhãn cho cùng câu hỏi; với API thật các phiếu có thể khác nhau.")
print("\nCả lần chạy:", so.bao_cao())
