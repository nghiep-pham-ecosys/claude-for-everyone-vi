"""Module 08 — routing: một lời gọi phân loại, code chọn hàm xử lý theo nhãn.

Phân loại bằng structured outputs có `enum`, nên nhãn luôn nằm trong danh sách. Code vẫn giữ nhánh dự phòng:
stop_reason khác "end_turn", JSON hỏng, hay một nhãn mới thêm vào schema mà quên viết hàm xử lý.

Mock không hiểu câu hỏi: nó chọn nhãn có từ khoá xuất hiện trong lượt user, không có thì nhãn đầu tiên.
Vì vậy "khac" đứng đầu enum, và lượt user chỉ chứa câu hỏi (chỉ dẫn phân loại nằm trong system).

Chạy:  CLAUDE_MOCK=1 uv run python modules/08-agents-workflows/python/03_dinh_tuyen.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from phong_thi_nghiem import TOOLS_MOI_TRUONG, TRA_AQI, TRA_NHIET_DO, SoChiPhi, doc_trang, tao_client  # noqa: E402

from claude_vi import text_of  # noqa: E402

NHAN = ["khac", "quy_trinh", "so_lieu"]
SCHEMA = {"type": "object", "properties": {"nhan": {"type": "string", "enum": NHAN}},
          "required": ["nhan"], "additionalProperties": False}
SYSTEM_PHAN_LOAI = (
    "Phân loại câu hỏi của người dùng phòng thí nghiệm. quy_trinh: hỏi cách làm, các bước, mã lỗi thiết bị. "
    "so_lieu: hỏi số đo môi trường hiện tại (AQI, nhiệt độ). khac: mọi câu còn lại."
)

client = tao_client()
so = SoChiPhi()


def quy_trinh(cau_hoi: str) -> str:
    tai_lieu = doc_trang("01_hieu_chuan_ph") + "\n\n" + doc_trang("02_ma_loi_md300")
    msg = so.ghi(client.ask(f"<tai_lieu>\n{tai_lieu}\n</tai_lieu>\n\n{cau_hoi}", system="Chỉ dựa vào tài liệu."))
    return text_of(msg)


def so_lieu(cau_hoi: str) -> str:
    """Vòng tool ngắn của module 03, có trần lượt."""
    tools, messages = [TRA_AQI, TRA_NHIET_DO], [{"role": "user", "content": cau_hoi}]
    for _ in range(4):
        msg = so.ghi(client.create(messages=messages, tools=tools))
        if msg.stop_reason != "tool_use":
            return text_of(msg)
        messages.append({"role": "assistant", "content": msg.content})
        messages.append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": b.id,
             "content": json.dumps(TOOLS_MOI_TRUONG[b.name](**b.input), ensure_ascii=False)}
            for b in msg.content if b.type == "tool_use"]})
    return "Chưa trả lời xong sau 4 lượt."


def khac(cau_hoi: str) -> str:
    return "Trợ lý chỉ trả lời về quy trình đo và số liệu môi trường."   # không tốn lời gọi nào


def du_phong(cau_hoi: str) -> str:
    return "Chưa phân loại được câu hỏi; chuyển cho người phụ trách."


XU_LY = {"quy_trinh": quy_trinh, "so_lieu": so_lieu, "khac": khac}


def dinh_tuyen(cau_hoi: str) -> tuple[str, str]:
    msg = so.ghi(client.ask(cau_hoi, system=SYSTEM_PHAN_LOAI,
                            output_config={"format": {"type": "json_schema", "schema": SCHEMA}}))
    try:
        nhan = json.loads(text_of(msg))["nhan"] if msg.stop_reason == "end_turn" else None
    except (json.JSONDecodeError, KeyError):
        nhan = None
    ham = XU_LY.get(nhan)
    return (nhan, ham(cau_hoi)) if ham else ("du_phong", du_phong(cau_hoi))


for cau in ["Quy trình hiệu chuẩn máy đo pH gồm những bước nào?",
            "Số liệu AQI ở Hà Nội lúc này là bao nhiêu?",
            "Trưa nay nên ăn món gì?"]:
    nhan, tra_loi = dinh_tuyen(cau)
    print(f"{cau}\n  -> {nhan}: {tra_loi[:90]}")
print("\nCả lần chạy:", so.bao_cao())
