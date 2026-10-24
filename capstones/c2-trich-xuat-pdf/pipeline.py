"""Capstone c2 — trích xuất số liệu thí nghiệm từ PDF ra JSON, kèm trang gốc đã kiểm chứng.

Lượt 1 (citations):           PDF + citations.enabled  -> trích dẫn nguyên văn, kèm số trang do API trả
Lượt 2 (structured outputs):  danh sách trích dẫn       -> JSON đúng schema, mỗi dòng trỏ về một trích dẫn
Bước 3 (code, không gọi API): đối chiếu từng dòng với text của trang PDF gốc

Hai lượt tách riêng vì citations và structured outputs không dùng chung được trong một request.

Chạy:  CLAUDE_MOCK=1 uv run python capstones/c2-trich-xuat-pdf/pipeline.py
       CLAUDE_MOCK=1 uv run python capstones/c2-trich-xuat-pdf/pipeline.py --cham exercises   # dùng code của bạn
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "py"))

from claude_vi import ClaudeVi, estimate_cost_usd  # noqa: E402

THU_MUC = Path(__file__).resolve().parent
PDF_MAU = THU_MUC / "data" / "bao_cao_thi_nghiem.pdf"


def nap_bai(thu_muc: str) -> ModuleType:
    import importlib.util

    ten = f"c2_{thu_muc}"
    spec = importlib.util.spec_from_file_location(ten, THU_MUC / thu_muc / "trich_xuat.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[ten] = mod  # dataclass cần module có trong sys.modules
    spec.loader.exec_module(mod)
    return mod


def doc_trang_pdf(pdf: bytes) -> list[str]:
    """Text của từng trang (trang 1 ở chỉ số 0) — dùng để kiểm chứng, không gửi cho Claude."""
    from pypdf import PdfReader

    return [page.extract_text() or "" for page in PdfReader(io.BytesIO(pdf)).pages]


def yeu_cau_trich_dan(pdf: bytes, tieu_de: str) -> dict[str, Any]:
    return {
        "system": "Bạn là trợ lý phòng thí nghiệm, đọc báo cáo và trích dẫn chính xác.",
        "messages": [{"role": "user", "content": [
            # docs PDF support: đặt PDF trước phần text của câu hỏi
            {"type": "document", "title": tieu_de, "citations": {"enabled": True},
             "source": {"type": "base64", "media_type": "application/pdf", "data": base64.b64encode(pdf).decode()}},
            {"type": "text", "text": (
                "Trích nguyên văn mọi câu chứa kết quả đo của các mẫu thí nghiệm (giá trị và đơn vị). "
                "Mỗi câu một trích dẫn. Không diễn giải, không tóm tắt.")},
        ]}],
    }


def chay(client: ClaudeVi, pdf: bytes, bai: ModuleType, tieu_de: str = "Báo cáo thí nghiệm") -> dict[str, Any]:
    msg1 = client.create(**yeu_cau_trich_dan(pdf, tieu_de))
    trich_dan = bai.doc_trich_dan(msg1)

    msg2 = client.create(**bai.yeu_cau_cau_truc(trich_dan))
    if msg2.stop_reason != "end_turn":
        raise RuntimeError(f"Lượt 2 chưa xong: stop_reason={msg2.stop_reason}")
    phep_do = json.loads(next(b.text for b in msg2.content if b.type == "text"))["phep_do"]

    bang = bai.kiem_chung(phep_do, trich_dan, doc_trang_pdf(pdf))
    return {
        "trich_dan": [vars(t) for t in trich_dan],
        "phep_do": bang,
        "chi_phi_usd": round(estimate_cost_usd(msg1) + estimate_cost_usd(msg2), 8),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", type=Path, default=PDF_MAU)
    ap.add_argument("--cham", default="solutions", choices=["solutions", "exercises"])
    ap.add_argument("--ra", type=Path, help="ghi kết quả JSON ra file")
    args = ap.parse_args(argv)

    ket_qua = chay(ClaudeVi(), args.pdf.read_bytes(), nap_bai(args.cham))
    text = json.dumps(ket_qua, ensure_ascii=False, indent=2)
    if args.ra:
        args.ra.write_text(text, "utf-8")
    print(text)
    ok = sum(d["da_kiem_chung"] for d in ket_qua["phep_do"])
    print(f"\n{len(ket_qua['trich_dan'])} trích dẫn, {ok}/{len(ket_qua['phep_do'])} dòng kiểm chứng được, "
          f"chi phí ước tính ${ket_qua['chi_phi_usd']:.6f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
