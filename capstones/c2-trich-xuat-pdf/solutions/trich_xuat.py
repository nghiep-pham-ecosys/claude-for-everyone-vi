"""Capstone c2 — ba hàm cốt lõi của pipeline. (LỜI GIẢI)"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from anthropic.types import Message


@dataclass(frozen=True)
class TrichDan:
    """Một trích dẫn lấy từ citations của API: id do ta đặt, trang và văn bản do API trả về."""
    id: str
    trang: int
    van_ban: str

TRUONG = ["nguon", "thi_nghiem", "mau", "dai_luong", "gia_tri", "don_vi"]


def doc_trich_dan(msg: Message) -> list[TrichDan]:
    if msg.stop_reason != "end_turn":
        raise ValueError(f"Lượt trích dẫn chưa xong: stop_reason={msg.stop_reason}")
    ket_qua: list[TrichDan] = []
    da_co: set[tuple[int, str]] = set()
    for block in msg.content:
        if block.type != "text":
            continue
        for cit in block.citations or []:
            if cit.type != "page_location":
                continue
            khoa = (cit.start_page_number, cit.cited_text.strip())
            if khoa in da_co:
                continue
            da_co.add(khoa)
            ket_qua.append(TrichDan(id=f"C{len(ket_qua) + 1}", trang=khoa[0], van_ban=khoa[1]))
    return ket_qua


def yeu_cau_cau_truc(trich_dan: list[TrichDan]) -> dict[str, Any]:
    if not trich_dan:
        raise ValueError("Không có trích dẫn nào để chuyển thành bảng")
    dong = {
        "type": "object",
        "properties": {
            "nguon": {"type": "string", "enum": [t.id for t in trich_dan],
                      "description": "id của trích dẫn chứa số liệu này"},
            "thi_nghiem": {"type": "string", "description": "mã hoặc tên thí nghiệm, ví dụ LR-2026-07"},
            "mau": {"type": "string", "description": "mã mẫu, ví dụ A1"},
            "dai_luong": {"type": "string", "description": "đại lượng đo, giữ nguyên tiếng Anh như tài liệu"},
            "gia_tri": {"type": "number"},
            "don_vi": {"type": "string", "description": "đơn vị như trong tài liệu; chuỗi rỗng nếu không có"},
        },
        "required": TRUONG,
        "additionalProperties": False,
    }
    schema = {"type": "object", "properties": {"phep_do": {"type": "array", "items": dong}},
              "required": ["phep_do"], "additionalProperties": False}
    khoi = "\n".join(f'<trich_dan id="{t.id}" trang="{t.trang}">{t.van_ban}</trich_dan>' for t in trich_dan)
    return {
        "system": ("Bạn chuyển trích dẫn từ báo cáo thí nghiệm thành bảng số liệu. Chỉ dùng con số xuất hiện "
                   "trong trích dẫn, không tính toán hay suy đoán thêm, vì bảng sẽ được đối chiếu tự động với PDF gốc."),
        "messages": [{"role": "user", "content": (
            f"<danh_sach_trich_dan>\n{khoi}\n</danh_sach_trich_dan>\n\n"
            "Tách mỗi phép đo thành một dòng: mỗi đại lượng của mỗi mẫu là một dòng riêng.")}],
        "output_config": {"format": {"type": "json_schema", "schema": schema}},
    }


def _chuan_hoa(text: str) -> str:
    return " ".join(text.split())


def _cac_so(text: str) -> list[float]:
    return [float(s.replace(",", ".")) for s in re.findall(r"-?\d+(?:[.,]\d+)?", text)]


def kiem_chung(phep_do: list[dict[str, Any]], trich_dan: list[TrichDan], trang_pdf: list[str]) -> list[dict[str, Any]]:
    theo_id = {t.id: t for t in trich_dan}
    ket_qua = []
    for dong in phep_do:
        td = theo_id.get(dong["nguon"])
        ly_do = None
        if td is None:
            ly_do = f"nguồn {dong['nguon']} không tồn tại"
        elif not 1 <= td.trang <= len(trang_pdf) or _chuan_hoa(td.van_ban) not in _chuan_hoa(trang_pdf[td.trang - 1]):
            ly_do = f"trích dẫn không tìm thấy ở trang {td.trang} của PDF"
        elif not any(abs(so - dong["gia_tri"]) < 1e-9 for so in _cac_so(td.van_ban)):
            ly_do = f"giá trị {dong['gia_tri']} không có trong trích dẫn"
        ket_qua.append({**dong, "trang": td.trang if td else None, "trich_dan": td.van_ban if td else None,
                        "da_kiem_chung": ly_do is None, "ly_do": ly_do})
    return ket_qua
