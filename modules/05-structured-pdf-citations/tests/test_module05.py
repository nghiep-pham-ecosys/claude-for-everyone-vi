"""Chấm tự động bài tập module 05 (mock mode, không gọi mạng).

    uv run pytest modules/05-structured-pdf-citations -q                    # chấm lời giải
    CHAM=exercises uv run pytest modules/05-structured-pdf-citations -q     # chấm bài của bạn
"""
import base64
import json
from pathlib import Path

import pytest
from anthropic.types import Message
from claude_vi import check_request
from claude_vi.cham import nap as _nap
from claude_vi.cham import tao_client
from claude_vi.rules import schema_errors

MODULE = Path(__file__).resolve().parents[1]
PDF = (MODULE.parents[1] / "capstones" / "c2-trich-xuat-pdf" / "data" / "bao_cao_thi_nghiem.pdf").read_bytes()
VAN_BAN = "Phiếu GK-03. Mẫu W1 có pH 7.1 và DO 6.2 mg/L. Mẫu W2 có pH 6.4."


def nap(ten: str):
    return _nap(MODULE, ten)


def message(blocks, stop_reason="end_turn") -> Message:
    return Message.model_validate({
        "id": "msg_t", "type": "message", "role": "assistant", "model": "claude-haiku-5-5",
        "content": [{"type": "thinking", "thinking": "", "signature": "s"}, *blocks],
        "stop_reason": stop_reason, "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 1},
    })


def text(t, *cits):
    return {"type": "text", "text": t, "citations": list(cits) or None}


def char(cited, start, end, doc=0):
    return {"type": "char_location", "cited_text": cited, "document_index": doc, "document_title": None,
            "start_char_index": start, "end_char_index": end}


def doc_text(data=VAN_BAN):
    return {"type": "document", "source": {"type": "text", "media_type": "text/plain", "data": data},
            "citations": {"enabled": True}}


def doc_pdf():
    return {"type": "document", "citations": {"enabled": True},
            "source": {"type": "base64", "media_type": "application/pdf", "data": base64.b64encode(PDF).decode()}}


def doc_khoi(*dong):
    return {"type": "document", "citations": {"enabled": True},
            "source": {"type": "content", "content": [{"type": "text", "text": d} for d in dong]}}


# ---------- Bài 1 ----------

def test_bai1_schema_gui_duoc_va_giu_rang_buoc():
    params = nap("bai1_phieu_nuoc").yeu_cau_phieu("W1: pH 7,1; DO 6,2 mg/L; đạt.")
    check_request({"model": "claude-haiku-5-5", **params})                  # không lỗi 400
    schema = params["output_config"]["format"]["schema"]
    assert schema_errors(schema) == []
    assert set(schema["required"]) == {"ma_mau", "ph", "do_mg_l", "danh_gia"}  # ghi_chu là optional
    assert set(schema["properties"]["danh_gia"]["enum"]) == {"dat", "khong_dat"}
    assert "minimum" not in schema["properties"]["ph"] and "maximum" not in schema["properties"]["ph"]
    assert "maximum: 14" in schema["properties"]["ph"]["description"]        # transform_schema chép vào mô tả
    assert "<van_ban>W1: pH 7,1; DO 6,2 mg/L; đạt.</van_ban>" in json.dumps(params["messages"], ensure_ascii=False)
    assert params["messages"][-1]["role"] == "user" and params.get("system")


def test_bai1_chay_qua_mock():
    b1 = nap("bai1_phieu_nuoc")
    client, _ = tao_client()
    phieu = b1.doc_phieu(client.create(**b1.yeu_cau_phieu("W1: pH 7,1")))
    assert phieu.ma_mau == "[MOCK]" and phieu.danh_gia == "dat"


def test_bai1_chuan_hoa_enum():
    b1 = nap("bai1_phieu_nuoc")
    phieu = b1.doc_phieu(message([text('{"ma_mau": "W1", "ph": 7.1, "do_mg_l": 6.2, "danh_gia": "Dat"}')]))
    assert phieu.danh_gia == "dat" and phieu.ghi_chu is None and phieu.ph == 7.1


@pytest.mark.parametrize("t,stop", [
    ('{"ma_mau": "W1", "ph": 15, "do_mg_l": 6.2, "danh_gia": "dat"}', "end_turn"),     # pH ngoài 0–14
    ('{"ma_mau": "W1", "ph": 7, "do_mg_l": -1, "danh_gia": "dat"}', "end_turn"),       # DO âm
    ('{"ma_mau": "W1", "ph": 7, "do_mg_l": 6, "danh_gia": "tot"}', "end_turn"),        # enum lạ
    ('{"ma_mau": "W1", "ph": 7', "max_tokens"),
])
def test_bai1_bao_loi(t, stop):
    with pytest.raises(ValueError):
        nap("bai1_phieu_nuoc").doc_phieu(message([text(t)], stop))


# ---------- Bài 2 ----------

def test_bai2_van_ban_qua_mock():
    b2 = nap("bai2_kiem_trich_dan")
    client, _ = tao_client()
    tai_lieu = [doc_text()]
    msg = client.create(messages=[{"role": "user", "content": [*tai_lieu, {"type": "text", "text": "?"}]}])
    td = b2.doc_trich_dan(msg, tai_lieu)
    assert td and all(t.hop_le for t in td)
    w1 = next(t for t in td if "W1" in t.cited_text)
    assert w1.vi_tri == f"ký tự {VAN_BAN.index('Mẫu W1')}–{VAN_BAN.index('Mẫu W1') + len(w1.cited_text)}"
    assert w1.tai_lieu == 0 and w1.ly_do is None


def test_bai2_ba_loai_tai_lieu_qua_mock():
    b2 = nap("bai2_kiem_trich_dan")
    client, _ = tao_client()
    tai_lieu = [doc_pdf(), doc_text(), doc_khoi("Mở máy", "W1: pH 7.1, 26.5 °C")]
    msg = client.create(messages=[{"role": "user", "content": [*tai_lieu, {"type": "text", "text": "?"}]}])
    td = b2.doc_trich_dan(msg, tai_lieu)
    assert {t.tai_lieu for t in td} == {0, 1, 2} and all(t.hop_le for t in td)
    assert any(t.vi_tri == "trang 1–2" for t in td if t.tai_lieu == 0)
    assert [t.vi_tri for t in td if t.tai_lieu == 2] == ["khối 1–2"]


def test_bai2_bat_trich_dan_sai():
    b2 = nap("bai2_kiem_trich_dan")
    w1 = "Mẫu W1 có pH 7.1 và DO 6.2 mg/L."
    s = VAN_BAN.index(w1)
    msg = message([
        text("W1 đạt", char(w1, s, s + len(w1))),                                  # đúng
        text("W1 lệch", char(w1, s + 1, s + 1 + len(w1))),                         # lệch chỉ số
        text("tài liệu ma", char(w1, s, s + len(w1), doc=3)),                      # document_index sai
        text("trang 3", {"type": "page_location", "cited_text": "Specimen A1", "document_index": 1,
                         "document_title": None, "start_page_number": 3, "end_page_number": 4}),
        text("trang 2", {"type": "page_location", "cited_text": "Specimen A1: yield strength 276 MPa",
                         "document_index": 1, "document_title": None, "start_page_number": 2, "end_page_number": 3}),
        text("khối 5", {"type": "content_block_location", "cited_text": "x", "document_index": 2,
                        "document_title": None, "start_block_index": 5, "end_block_index": 6}),
    ])
    td = b2.doc_trich_dan(msg, [doc_text(), doc_pdf(), doc_khoi("a", "b")])
    assert [t.hop_le for t in td] == [True, False, False, False, False, False]
    assert all(t.ly_do for t in td[1:])
    assert td[1].vi_tri == f"ký tự {s + 1}–{s + 1 + len(w1)}"


def test_bai2_loai_vi_tri_khong_khop_loai_tai_lieu():
    b2 = nap("bai2_kiem_trich_dan")
    msg = message([text("x", char("Mở máy", 0, 6))])
    assert not b2.doc_trich_dan(msg, [doc_khoi("Mở máy")])[0].hop_le


def test_bai2_chua_xong_thi_bao_loi():
    with pytest.raises(ValueError):
        nap("bai2_kiem_trich_dan").doc_trich_dan(message([text("x")], "max_tokens"), [doc_text()])


# ---------- Bài 3 ----------

TRUONG = ["ma_mau", "ph", "gio_lay"]
NGUON = "Mẫu W1 lấy lúc 08:20, pH 7.1."


def test_bai3_yeu_cau_hop_le():
    b3 = nap("bai3_truong_kem_trich_dan")
    goc = {"type": "document", "source": {"type": "text", "media_type": "text/plain", "data": NGUON}}
    params = b3.yeu_cau_truong(goc, TRUONG)
    check_request({"model": "claude-haiku-5-5", **params})
    assert "output_config" not in params
    content = params["messages"][-1]["content"]
    assert content[0]["type"] == "document" and content[0]["citations"] == {"enabled": True}
    assert "citations" not in goc                                             # không sửa dict của người gọi
    prompt = " ".join(b["text"] for b in content if b["type"] == "text")
    assert all(t in prompt for t in TRUONG) and "JSON" not in prompt.upper()
    with pytest.raises(ValueError):
        b3.yeu_cau_truong(goc, [])


def test_bai3_tach_theo_docs():
    b3 = nap("bai3_truong_kem_trich_dan")
    c = char(NGUON, 0, len(NGUON))
    msg = message([
        text("ma_mau: "), text("W1", c),                       # citation chỉ trên phần giá trị
        text("\nph: 7.1", c),                                   # citation trên cả dòng, sau "\n"
        text("\ngio_lay: "), text("08:20", c),                  # giá trị có dấu hai chấm
        text("\nnhiet_do: 26 °C", c),                           # trường lạ -> bỏ
        text("\nHết danh sách"),                                # không có dấu hai chấm -> bỏ
    ])
    kq = b3.tach_truong(msg, TRUONG)
    assert kq == {"ma_mau": {"gia_tri": "W1", "trich_dan": [NGUON]},
                  "ph": {"gia_tri": "7.1", "trich_dan": [NGUON]},
                  "gio_lay": {"gia_tri": "08:20", "trich_dan": [NGUON]}}
    assert b3.truong_thieu(kq, TRUONG) == []


def test_bai3_bao_truong_thieu():
    b3 = nap("bai3_truong_kem_trich_dan")
    c = char(NGUON, 0, len(NGUON))
    msg = message([text("ma_mau: W1\n", c), text("ph: 7.1\ngio_lay: \n"), text("ma_mau: W9", c)])
    kq = b3.tach_truong(msg, TRUONG)
    assert kq["ma_mau"]["gia_tri"] == "W1"                                   # lặp lại -> giữ lần đầu
    assert kq["ph"] == {"gia_tri": "7.1", "trich_dan": []}
    assert b3.truong_thieu(kq, TRUONG) == ["ph", "gio_lay"]


def test_bai3_chay_qua_mock():
    b3 = nap("bai3_truong_kem_trich_dan")
    client, _ = tao_client()
    goc = {"type": "document", "source": {"type": "text", "media_type": "text/plain", "data": NGUON}}
    msg = client.create(**b3.yeu_cau_truong(goc, TRUONG))
    assert b3.truong_thieu(b3.tach_truong(msg, TRUONG), TRUONG) == TRUONG    # mock không theo định dạng


def test_bai3_chua_xong_thi_bao_loi():
    with pytest.raises(ValueError):
        nap("bai3_truong_kem_trich_dan").tach_truong(message([text("ph: 7")], "refusal"), TRUONG)
