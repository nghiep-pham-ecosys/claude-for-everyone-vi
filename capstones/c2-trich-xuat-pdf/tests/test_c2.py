"""Chấm capstone c2 (mock mode, không gọi mạng).

    uv run pytest capstones/c2-trich-xuat-pdf -q                    # chấm lời giải
    CHAM=exercises uv run pytest capstones/c2-trich-xuat-pdf -q     # chấm bài của bạn
"""
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest
from anthropic.types import Message

from claude_vi import ClaudeVi, check_request
from claude_vi.cham import SETTINGS
from claude_vi.cham import nap as _nap
from claude_vi.mock import MockAnthropic, request_key

CAPSTONE = Path(__file__).resolve().parents[1]
PDF = (CAPSTONE / "data" / "bao_cao_thi_nghiem.pdf").read_bytes()


def nap():
    return _nap(CAPSTONE, "trich_xuat")


def pipeline():
    spec = importlib.util.spec_from_file_location("c2_pipeline", CAPSTONE / "pipeline.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["c2_pipeline"] = mod
    spec.loader.exec_module(mod)
    return mod


def message(blocks, stop_reason="end_turn"):
    return Message.model_validate({
        "id": "m", "type": "message", "role": "assistant", "model": "claude-haiku-5-5", "content": blocks,
        "stop_reason": stop_reason, "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 1}})


def cit(text, page):
    return {"type": "page_location", "cited_text": text, "document_index": 0, "document_title": "BC",
            "start_page_number": page, "end_page_number": page + 1}


A1 = "Specimen A1: yield strength 276 MPa, tensile strength 310 MPa, elongation 12.1 %."
W3A = "Sample W3-a: pH 7.2, dissolved oxygen 6.8 mg/L, turbidity 14 NTU."


def test_pdf_mau_khop_voi_script_sinh():
    spec = importlib.util.spec_from_file_location("tao_pdf_mau", CAPSTONE / "data" / "tao_pdf_mau.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.build_pdf() == PDF          # PDF trong repo sinh lại được, không ai sửa tay


# ---------- doc_trich_dan ----------

def test_doc_trich_dan_tu_citations():
    b = nap()
    msg = message([
        {"type": "thinking", "thinking": "", "signature": "s"},
        {"type": "text", "text": "Các câu: "},
        {"type": "text", "text": "A1 ...", "citations": [cit(A1 + "  ", 1)]},
        {"type": "text", "text": "W3-a ...", "citations": [cit(W3A, 2), cit(A1, 1)]},   # A1 lặp lại
    ])
    td = b.doc_trich_dan(msg)
    assert [(t.id, t.trang, t.van_ban) for t in td] == [("C1", 1, A1), ("C2", 2, W3A)]


def test_doc_trich_dan_bo_qua_loai_khac_va_bao_loi_khi_cat():
    b = nap()
    char = {"type": "char_location", "cited_text": "x 1 2.", "document_index": 0, "document_title": None,
            "start_char_index": 0, "end_char_index": 6}
    assert b.doc_trich_dan(message([{"type": "text", "text": "x", "citations": [char]}])) == []
    with pytest.raises(ValueError):
        b.doc_trich_dan(message([{"type": "text", "text": "x", "citations": [cit(A1, 1)]}], "max_tokens"))


def test_doc_trich_dan_qua_mock_pdf_that():
    b = nap()
    p = pipeline()
    client = ClaudeVi(settings=SETTINGS, client=MockAnthropic())
    td = b.doc_trich_dan(client.create(**p.yeu_cau_trich_dan(PDF, "BC")))
    assert {t.trang for t in td} == {1, 2}
    assert next(t for t in td if t.van_ban == A1).trang == 1


# ---------- yeu_cau_cau_truc ----------

def test_yeu_cau_cau_truc_hop_le():
    b = nap()
    td = [b.TrichDan("C1", 1, A1), b.TrichDan("C2", 2, W3A)]
    params = b.yeu_cau_cau_truc(td)
    check_request({"model": "claude-haiku-5-5", **params})                     # không lỗi 400
    noi_dung = " ".join(str(m["content"]) for m in params["messages"])
    assert "application/pdf" not in noi_dung and "citations" not in noi_dung   # không gửi lại PDF
    assert '<trich_dan id="C1" trang="1">' in noi_dung and A1 in noi_dung
    dong = params["output_config"]["format"]["schema"]["properties"]["phep_do"]["items"]
    assert dong["properties"]["nguon"]["enum"] == ["C1", "C2"]
    assert set(dong["required"]) == set(b.TRUONG) and dong["properties"]["gia_tri"]["type"] == "number"
    assert "system" in params


def test_yeu_cau_cau_truc_rong():
    with pytest.raises(ValueError):
        nap().yeu_cau_cau_truc([])


# ---------- kiem_chung ----------

TRANG = ["header\n" + A1 + "\nfooter", "header\n" + W3A]


def dong(nguon, gia_tri):
    return {"nguon": nguon, "thi_nghiem": "LR", "mau": "A1", "dai_luong": "q", "gia_tri": gia_tri, "don_vi": "u"}


@pytest.mark.parametrize("phep_do,trich_dan_trang,ok,can", [
    (dong("C1", 276), 1, True, None),
    (dong("C1", 12.1), 1, True, None),
    (dong("C2", 7.2), 2, True, None),
    (dong("C1", 290), 1, False, "không có trong trích dẫn"),        # số bịa
    (dong("C1", 276), 2, False, "không tìm thấy"),                  # trích dẫn gán sai trang
    (dong("C9", 276), 1, False, "không tồn tại"),
])
def test_kiem_chung(phep_do, trich_dan_trang, ok, can):
    b = nap()
    td = [b.TrichDan("C1", trich_dan_trang, A1), b.TrichDan("C2", 2, W3A)]
    (kq,) = b.kiem_chung([phep_do], td, TRANG)
    assert kq["da_kiem_chung"] is ok
    assert {k: kq[k] for k in phep_do} == phep_do                     # giữ nguyên dữ liệu gốc
    if ok:
        assert kq["ly_do"] is None and kq["trang"] == trich_dan_trang
    else:
        assert can in kq["ly_do"]


def test_kiem_chung_dau_phay_thap_phan_va_khoang_trang():
    b = nap()
    td = [b.TrichDan("C1", 1, "pH   7,2  tại trạm.")]
    (kq,) = b.kiem_chung([dong("C1", 7.2)], td, ["Kết quả: pH 7,2 tại trạm. Hết."])
    assert kq["da_kiem_chung"] is True


# ---------- cả pipeline ----------

def test_pipeline_end_to_end_voi_fixture(tmp_path):
    """Lượt 2 dùng fixture viết tay (được phép trong test) để mô phỏng một câu trả lời tốt + một dòng bịa."""
    b = nap()
    p = pipeline()
    mock = MockAnthropic(record_dir=tmp_path)
    client = ClaudeVi(settings=SETTINGS, client=mock)
    td = b.doc_trich_dan(client.create(**p.yeu_cau_trich_dan(PDF, "Báo cáo thí nghiệm")))
    c_a1 = next(t.id for t in td if t.van_ban == A1)

    params2 = {"model": SETTINGS.model, **b.yeu_cau_cau_truc(td)}
    bang = {"phep_do": [dong(c_a1, 276), dong(c_a1, 999)]}
    (tmp_path / f"{request_key(params2)}.json").write_text(json.dumps({
        "id": "m2", "type": "message", "role": "assistant", "model": SETTINGS.model,
        "content": [{"type": "text", "text": json.dumps(bang)}], "stop_reason": "end_turn",
        "stop_sequence": None, "usage": {"input_tokens": 300, "output_tokens": 80}}), "utf-8")

    kq = p.chay(client, PDF, b)
    assert [d["da_kiem_chung"] for d in kq["phep_do"]] == [True, False]
    assert kq["phep_do"][0]["trang"] == 1 and kq["chi_phi_usd"] > 0


def test_pipeline_chay_duoc_o_mock_khong_fixture(capsys, monkeypatch):
    monkeypatch.setenv("CLAUDE_MOCK", "1")
    assert pipeline().main(["--cham", os.getenv("CHAM", "solutions")]) == 0
    assert "trích dẫn" in capsys.readouterr().out
