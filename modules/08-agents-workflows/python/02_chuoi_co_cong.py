"""Module 08 — prompt chaining có cổng kiểm (gate).

Bước 1 trích một phép đo bằng structured outputs. Cổng kiểm BẰNG CODE: đúng đại lượng, đúng đơn vị,
giá trị trong khoảng hợp lệ. Cổng trượt thì dừng chuỗi và nói rõ vì sao; bước 2 không được gọi.

Ở mock mode, số trong JSON luôn là 0 và chuỗi là "[MOCK]", nên cổng trượt: đó chính là điều script muốn cho thấy.
Phần cuối đưa một kết quả bước 1 hợp lệ (viết tay) qua cổng để thấy nhánh đi tiếp.

Chạy:  CLAUDE_MOCK=1 uv run python modules/08-agents-workflows/python/02_chuoi_co_cong.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from phong_thi_nghiem import doc_trang, tao_client  # noqa: E402

from claude_vi import text_of  # noqa: E402

# Khoảng hợp lệ và đơn vị lấy từ trang sổ tay 01 (hư cấu): độ dốc điện cực 95–105 %
KHOANG = {"do_doc_dien_cuc": (95.0, 105.0, "%")}
SCHEMA = {
    "type": "object",
    "properties": {
        "dai_luong": {"type": "string", "enum": list(KHOANG)},
        "gia_tri": {"type": "number"},
        "don_vi": {"type": "string"},
    },
    "required": ["dai_luong", "gia_tri", "don_vi"],
    "additionalProperties": False,
}


def cong_kiem(du_lieu: dict) -> str | None:
    """None nếu qua cổng, ngược lại là lý do trượt. Không gọi Claude: cổng là code, rẻ và chắc chắn."""
    lo, hi, don_vi = KHOANG[du_lieu["dai_luong"]]
    if du_lieu["don_vi"] != don_vi:
        return f"đơn vị '{du_lieu['don_vi']}' khác '{don_vi}'"
    if not lo <= du_lieu["gia_tri"] <= hi:
        return f"giá trị {du_lieu['gia_tri']} ngoài khoảng {lo}–{hi} {don_vi}"
    return None


def buoc_2(client, du_lieu: dict) -> str:
    msg = client.ask(f"Viết một câu nhận xét cho phép đo: {json.dumps(du_lieu, ensure_ascii=False)}",
                     system="Trả lời một câu, tiếng Việt.")
    return text_of(msg)


client = tao_client()
van_ban = doc_trang("01_hieu_chuan_ph") + "\n\nKết quả hôm nay: độ dốc điện cực đo được 98,6 %."
msg = client.ask(f"<van_ban>\n{van_ban}\n</van_ban>\n\nTrích phép đo của hôm nay.",
                 output_config={"format": {"type": "json_schema", "schema": SCHEMA}})
if msg.stop_reason != "end_turn":
    raise SystemExit(f"Bước 1 không xong (stop_reason={msg.stop_reason}): dừng chuỗi.")

du_lieu = json.loads(text_of(msg))
print("Bước 1 trả:", du_lieu)
ly_do = cong_kiem(du_lieu)
if ly_do:
    print("Cổng TRƯỢT:", ly_do, "-> dừng, không gọi bước 2.")
else:
    print("Cổng qua. Bước 2:", buoc_2(client, du_lieu))

hop_le = {"dai_luong": "do_doc_dien_cuc", "gia_tri": 98.6, "don_vi": "%"}
print("\nVới kết quả bước 1 hợp lệ", hop_le)
print("Cổng:", cong_kiem(hop_le) or "qua", "-> bước 2:", buoc_2(client, hop_le))
