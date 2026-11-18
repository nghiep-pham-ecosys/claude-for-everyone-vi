"""Module 08 — vòng lặp agent tự viết, đủ điều kiện dừng.

Từ vòng tool của module 03, thêm:
  - dừng khi stop_reason == "end_turn"; dừng khi hết số lượt; dừng khi lời gọi TIẾP THEO có thể vượt trần chi phí
    (kiểm TRƯỚC khi gọi, bằng trần output theo max_tokens, module 06 mục 3);
  - stop_reason == "max_tokens" giữa vòng: text có thể rỗng vì thinking dùng hết trần (module 07 mục 4) -> dừng, báo rõ;
  - lịch sử append-only: gửi lại lượt assistant nguyên vẹn, không rút gọn tool_result cũ, không đổi `system`;
  - nhắc ở lượt cuối bằng một message `system` đặt sau lượt user chứa tool_result, không sửa tham số `system`.

Mock ở script này bật multi_step: mỗi lượt gọi MỘT tool chưa có kết quả, đủ thì trả lời. Mock không đọc lời nhắc.

Chạy:  CLAUDE_MOCK=1 uv run python modules/08-agents-workflows/python/07_vong_lap_agent.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from phong_thi_nghiem import (  # noqa: E402
    TOOLS_MOI_TRUONG,
    TRA_AQI,
    TRA_NHIET_DO,
    SoChiPhi,
    doc_trang,
    tao_client,
    tool_doc_so_tay,
    tran_output_usd,
)

from claude_vi import text_of  # noqa: E402

SYSTEM = "Bạn là trợ lý phòng thí nghiệm (hư cấu). Dùng tool khi cần số liệu hoặc quy trình. Trả lời ngắn."
TOOLS = [tool_doc_so_tay(["03_lay_mau_nuoc", "06_an_toan"]), TRA_AQI, TRA_NHIET_DO]
REGISTRY = {"doc_so_tay": doc_trang, **TOOLS_MOI_TRUONG}
NHAC_LUOT_CUOI = "Đây là lượt cuối được phép. Hãy kết luận từ kết quả đã có, không gọi thêm tool."


def chay_tool(block) -> dict:
    """Một tool_result. Tool lạ hoặc tool lỗi -> is_error kèm lời nhắn có ích (module 03 mục 6)."""
    if block.name not in REGISTRY:
        return {"type": "tool_result", "tool_use_id": block.id, "is_error": True,
                "content": f"Không có tool '{block.name}'. Tool hiện có: {', '.join(REGISTRY)}."}
    try:
        out = REGISTRY[block.name](**block.input)
    except Exception as e:  # noqa: BLE001 - mọi lỗi của tool đều phải về tay Claude
        return {"type": "tool_result", "tool_use_id": block.id, "is_error": True, "content": f"{type(e).__name__}: {e}"}
    return {"type": "tool_result", "tool_use_id": block.id,
            "content": out if isinstance(out, str) else json.dumps(out, ensure_ascii=False)}


def chay_agent(client, cau_hoi: str, toi_da_luot: int = 6, tran_usd: float = 0.01):
    """Trả (lý do dừng, Message cuối hoặc None, SoChiPhi)."""
    so = SoChiPhi()
    tran_mot_loi_goi = tran_output_usd(client.settings.model, client.settings.max_tokens)
    messages = [{"role": "user", "content": cau_hoi}]
    msg = None
    for luot in range(1, toi_da_luot + 1):
        if so.usd + tran_mot_loi_goi > tran_usd:   # kiểm TRƯỚC khi gọi; input chưa biết nên đây là cận dưới
            return "tran_chi_phi", msg, so
        if luot == toi_da_luot and luot > 1:
            messages.append({"role": "system", "content": NHAC_LUOT_CUOI})
        msg = so.ghi(client.create(system=SYSTEM, messages=messages, tools=TOOLS))
        goi = [f"{b.name}{b.input}" for b in msg.content if b.type == "tool_use"]
        print(f"  lượt {luot}: stop_reason={msg.stop_reason} {' '.join(goi)}")
        if msg.stop_reason != "tool_use":
            return msg.stop_reason, msg, so   # end_turn, max_tokens, refusal, pause_turn...: người gọi quyết
        messages.append({"role": "assistant", "content": msg.content})   # nguyên vẹn, kể cả thinking
        messages.append({"role": "user", "content": [chay_tool(b) for b in msg.content if b.type == "tool_use"]})
    return "het_luot", msg, so


client = tao_client()
cau_hoi = "Chiều nay đi lấy mẫu nước ở Hà Nội: cần lưu ý gì về an toàn, không khí và nhiệt độ?"
tran_1 = tran_output_usd(client.settings.model, client.settings.max_tokens)

for ten, kwargs in [("Đủ lượt, đủ tiền", {}),
                    ("Trần 2 lượt", {"toi_da_luot": 2}),
                    ("Trần chi phí vừa đủ một lời gọi", {"tran_usd": tran_1 * 1.01})]:
    print(f"\n{ten}:")
    ly_do, msg, so = chay_agent(client, cau_hoi, **kwargs)
    print(f"  -> dừng vì {ly_do}; {so.bao_cao()}")
    if ly_do == "end_turn":
        print("  Trả lời:", text_of(msg)[:100].replace("\n", " "))
    elif ly_do == "max_tokens":
        print("  Bị cắt ở max_tokens: text có thể rỗng, đừng dùng như câu trả lời hoàn chỉnh.")
print(f"\nTrần output của MỘT lời gọi với max_tokens={client.settings.max_tokens}: ${tran_1:.6f}."
      "\nTrần chi phí thật của cả lần chạy còn phải cộng input, vốn lớn dần qua mỗi lượt.")
