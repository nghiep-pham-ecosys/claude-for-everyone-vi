"""Bài 1 — chuỗi hai bước có cổng kiểm. (LỜI GIẢI)"""
from __future__ import annotations

import json
from typing import Any

from claude_vi import ClaudeVi, text_of

# Khoảng hợp lệ và đơn vị của từng đại lượng (số liệu hư cấu)
GIOI_HAN = {
    "pH": (0.0, 14.0, ""),
    "nhiet_do_c": (-10.0, 60.0, "°C"),
    "do_doc_dien_cuc": (80.0, 120.0, "%"),
}
SCHEMA = {
    "type": "object",
    "properties": {
        "dai_luong": {"type": "string", "enum": list(GIOI_HAN)},
        "gia_tri": {"type": "number"},
        "don_vi": {"type": "string"},
    },
    "required": ["dai_luong", "gia_tri", "don_vi"],
    "additionalProperties": False,
}


def kiem_cong(du_lieu: Any) -> str | None:
    if not isinstance(du_lieu, dict):
        return "kết quả bước 1 không phải object"
    thieu = [k for k in ("dai_luong", "gia_tri", "don_vi") if k not in du_lieu]
    if thieu:
        return f"thiếu trường {', '.join(thieu)}"
    dai_luong, gia_tri = du_lieu["dai_luong"], du_lieu["gia_tri"]
    if dai_luong not in GIOI_HAN:
        return f"đại lượng lạ '{dai_luong}'"
    if isinstance(gia_tri, bool) or not isinstance(gia_tri, (int, float)):
        return f"giá trị '{gia_tri}' không phải số"
    lo, hi, don_vi = GIOI_HAN[dai_luong]
    if du_lieu["don_vi"] != don_vi:
        return f"đơn vị '{du_lieu['don_vi']}' khác '{don_vi}'"
    if not lo <= gia_tri <= hi:
        return f"giá trị {gia_tri} ngoài khoảng {lo}–{hi}"
    return None


def chuoi_hai_buoc(client: ClaudeVi, van_ban: str) -> dict[str, Any]:
    msg = client.ask(f"<van_ban>\n{van_ban}\n</van_ban>\n\nTrích phép đo trong văn bản.",
                     output_config={"format": {"type": "json_schema", "schema": SCHEMA}})
    if msg.stop_reason != "end_turn":
        return {"ok": False, "ly_do": f"bước 1 dừng vì {msg.stop_reason}", "phep_do": None, "tom_tat": None}
    try:
        du_lieu = json.loads(text_of(msg))
    except json.JSONDecodeError:
        return {"ok": False, "ly_do": "bước 1 trả JSON hỏng", "phep_do": None, "tom_tat": None}
    ly_do = kiem_cong(du_lieu)
    if ly_do:
        return {"ok": False, "ly_do": ly_do, "phep_do": du_lieu, "tom_tat": None}
    tom_tat = client.ask(f"Viết một câu tóm tắt phép đo: {json.dumps(du_lieu, ensure_ascii=False)}")
    return {"ok": True, "ly_do": None, "phep_do": du_lieu, "tom_tat": text_of(tom_tat)}
