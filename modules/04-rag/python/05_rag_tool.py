"""Module 04 — để Claude tự tìm: tool trả về search_result.

Script 04 luôn tìm trước rồi mới hỏi. Cách này để Claude quyết định có cần tìm không, tìm bằng từ khoá gì,
và tìm thêm nếu chưa đủ. Tool trả về danh sách search_result; không có kết quả thì trả một block text
nói rõ, đừng ném lỗi. tool_choice giữ "auto" (any/tool trả 400 trên Opus/Sonnet 5.5, Fable 5.x).

Chạy:  CLAUDE_MOCK=1 uv run python modules/04-rag/python/05_rag_tool.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from claude_vi import ClaudeVi, text_of  # noqa: E402
from rag_mau import hop, tat_ca_doan, tim  # noqa: E402

doan, texts = tat_ca_doan()
TIM_SO_TAY = {
    "name": "tim_so_tay",
    "description": ("Tìm trong sổ tay nội bộ của phòng thí nghiệm môi trường: quy trình lấy và bảo quản mẫu, "
                    "hiệu chuẩn và mã lỗi máy đo, an toàn, quản lý thiết bị. Dùng từ khoá cụ thể như mã lỗi, "
                    "mã thiết bị, tên chỉ tiêu. Trả về tối đa 3 đoạn liên quan nhất."),
    "strict": True,
    "input_schema": {"type": "object", "properties": {"tu_khoa": {"type": "string", "description": "từ khoá tìm kiếm"}},
                     "required": ["tu_khoa"], "additionalProperties": False},
}


def chay_tool(tu_khoa: str) -> list[dict]:
    tim_duoc = tim(doan, texts, tu_khoa, k=3)
    return hop.khoi_ket_qua(tim_duoc) if tim_duoc else [{"type": "text", "text": "Không tìm thấy đoạn nào."}]


client = ClaudeVi()
messages = [{"role": "user", "content": "Mẫu độ đục để được bao lâu trước khi phân tích?"}]
for luot in range(1, 5):
    msg = client.create(messages=messages, tools=[TIM_SO_TAY])
    messages.append({"role": "assistant", "content": msg.content})
    if msg.stop_reason != "tool_use":
        break
    ket_qua = []
    for call in (b for b in msg.content if b.type == "tool_use"):
        tu_khoa = call.input["tu_khoa"]
        if tu_khoa == "[MOCK]":                      # mock điền giá trị tối thiểu theo schema
            tu_khoa = "độ đục bảo quản"
        print(f"Lượt {luot}: Claude gọi tim_so_tay({tu_khoa!r})")
        ket_qua.append({"type": "tool_result", "tool_use_id": call.id, "content": chay_tool(tu_khoa)})
    messages.append({"role": "user", "content": ket_qua})

print("\nTrả lời:", text_of(msg))
for n in hop.nguon_trich_dan(msg):
    print(f"  nguồn {n['source']}: {n['cited_text']!r}")
