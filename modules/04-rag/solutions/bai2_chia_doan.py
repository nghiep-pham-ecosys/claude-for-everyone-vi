"""Bài 2 — chia tài liệu thành đoạn và thêm ngữ cảnh. (LỜI GIẢI)"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TaiLieu:
    ten: str          # tên file không đuôi, ví dụ "01_hieu_chuan_ph"
    noi_dung: str     # markdown đầy đủ


@dataclass(frozen=True)
class Doan:
    id: str           # "{ten}#{số thứ tự từ 1}"
    tieu_de: str      # dòng "# ..." của tài liệu
    muc: str          # dòng "## ..." chứa đoạn; "" nếu đoạn ở trước mục đầu tiên
    noi_dung: str


def chia_doan(tai_lieu: TaiLieu, max_ky_tu: int = 400) -> list[Doan]:
    tieu_de, muc = "", ""
    phan: list[tuple[str, list[str]]] = [("", [])]
    for dong in tai_lieu.noi_dung.splitlines():
        if dong.startswith("# "):
            tieu_de = dong[2:].strip()
        elif dong.startswith("## "):
            muc = dong[3:].strip()
            phan.append((muc, []))
        else:
            phan[-1][1].append(dong)
    doan: list[Doan] = []
    for ten_muc, dong in phan:
        doan_van = [p.strip() for p in "\n".join(dong).split("\n\n") if p.strip()]
        gom: list[str] = []
        for p in doan_van:
            if gom and len("\n\n".join([*gom, p])) > max_ky_tu:
                doan.append(Doan(f"{tai_lieu.ten}#{len(doan) + 1}", tieu_de, ten_muc, "\n\n".join(gom)))
                gom = []
            gom.append(p)
        if gom:
            doan.append(Doan(f"{tai_lieu.ten}#{len(doan) + 1}", tieu_de, ten_muc, "\n\n".join(gom)))
    return doan


def them_ngu_canh(doan: Doan) -> str:
    dau = f"Tài liệu: {doan.tieu_de}." + (f" Mục: {doan.muc}." if doan.muc else "")
    return f"{dau}\n{doan.noi_dung}"


def yeu_cau_ngu_canh(tai_lieu: TaiLieu, doan: Doan) -> dict[str, Any]:
    return {
        "max_tokens": 256,
        "output_config": {"effort": "low"},
        "messages": [{"role": "user", "content": (
            f"<document>\n{tai_lieu.noi_dung}\n</document>\n\n"
            f"<chunk>\n{doan.noi_dung}\n</chunk>\n\n"
            "Viết 1–2 câu ngắn đặt đoạn trên vào bối cảnh của cả tài liệu (đoạn nói về thiết bị, quy trình "
            "hay đối tượng nào), để đoạn này dễ được tìm thấy khi tra cứu. Chỉ trả về câu ngữ cảnh, không gì khác.")}],
    }
