"""Module 08 — orchestrator-workers: Claude lập danh sách việc con, mỗi worker làm một việc, một lời gọi tổng hợp.

Khác script 04: danh sách việc do Claude lập lúc chạy, không viết sẵn trong code.
Vì vậy code phải chặn độ dài danh sách (TOI_DA_VIEC) và chỉ cho chọn trang có thật (enum).
Mỗi việc con là một lời gọi nữa: in tổng số lời gọi và chi phí (module 06).

Chạy:  CLAUDE_MOCK=1 uv run python modules/08-agents-workflows/python/05_dieu_phoi.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from phong_thi_nghiem import SoChiPhi, danh_sach_trang, doc_trang, tao_client  # noqa: E402

from claude_vi import text_of  # noqa: E402

TOI_DA_VIEC = 4
SCHEMA = {
    "type": "object",
    "properties": {"viec_con": {"type": "array", "items": {
        "type": "object",
        "properties": {"trang": {"type": "string", "enum": danh_sach_trang()}, "cau_hoi": {"type": "string"}},
        "required": ["trang", "cau_hoi"], "additionalProperties": False}}},
    "required": ["viec_con"],
    "additionalProperties": False,
}

client = tao_client()
so = SoChiPhi()
yeu_cau = "Chuẩn bị ca đo nước sông ngày mai: cần lấy mẫu, bảo quản mẫu và hiệu chuẩn máy đo pH thế nào?"

# 1. Orchestrator: lập kế hoạch
LAP_KE_HOACH = (f"Chia yêu cầu thành tối đa {TOI_DA_VIEC} việc con. "
                "Mỗi việc con đọc đúng một trang sổ tay và trả lời một câu hỏi hẹp.")
msg = so.ghi(client.ask(yeu_cau, system=LAP_KE_HOACH,
                        output_config={"format": {"type": "json_schema", "schema": SCHEMA}}))
if msg.stop_reason != "end_turn":
    raise SystemExit(f"Không lập được kế hoạch (stop_reason={msg.stop_reason}).")
viec_con = json.loads(text_of(msg))["viec_con"]
if len(viec_con) > TOI_DA_VIEC:
    print(f"Kế hoạch có {len(viec_con)} việc, chỉ làm {TOI_DA_VIEC} việc đầu.")
    viec_con = viec_con[:TOI_DA_VIEC]   # structured outputs không hứa độ dài mảng: chặn bằng code
print("Kế hoạch:", viec_con)

# 2. Workers: mỗi việc một lời gọi (có thể chạy song song như script 04)
ket_qua = []
for v in viec_con:
    w = so.ghi(client.ask(f"<trang>\n{doc_trang(v['trang'])}\n</trang>\n\n{v['cau_hoi']}",
                          system="Chỉ dựa vào trang được đưa."))
    ket_qua.append(f"<ket_qua trang=\"{v['trang']}\">\n{text_of(w)}\n</ket_qua>")

# 3. Tổng hợp
cuoi = so.ghi(client.ask("\n".join(ket_qua) + f"\n\nDựa vào các kết quả trên, trả lời: {yeu_cau}"))
print("Tổng hợp:", text_of(cuoi)[:90])
print("Cả lần chạy:", so.bao_cao())
