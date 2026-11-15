"""Chấm tự động bài tập module 04 (mock mode, không gọi mạng).

    uv run pytest modules/04-rag -q                    # chấm lời giải
    CHAM=exercises uv run pytest modules/04-rag -q     # chấm bài của bạn
"""
import unicodedata
from pathlib import Path

import pytest
from anthropic.types import Message
from claude_vi import check_request
from claude_vi.cham import nap as _nap
from claude_vi.cham import tao_client

MODULE = Path(__file__).resolve().parents[1]
SO_TAY = MODULE / "data" / "so_tay"


def nap(ten: str):
    return _nap(MODULE, ten)


# ---------- Bài 1 ----------

def test_bai1_tach_tu():
    t = nap("bai1_bm25").tach_tu
    assert t("Lỗi E-17 trên MD-300: pH 7,00; nhiệt độ 26.5 °C. Đồng hồ") == \
        ["lỗi", "e-17", "trên", "md-300", "ph", "7,00", "nhiệt", "độ", "26.5", "c", "đồng", "hồ"]
    assert t("Lỗi E-17; Đồng hồ", bo_dau=True) == ["loi", "e-17", "dong", "ho"]
    assert t(unicodedata.normalize("NFD", "Hiệu chuẩn")) == ["hiệu", "chuẩn"]      # gõ kiểu tổ hợp


DOCS = [["ph", "do", "ph"], ["e-17", "loi"], ["ph", "loi", "may", "do", "nhanh"]]


def test_bai1_bm25_dung_cong_thuc():
    b = nap("bai1_bm25")
    m = b.BM25().fit(DOCS)
    assert m.idf("ph") == pytest.approx(0.47, abs=1e-4)                 # ln(1 + 1.5/2.5)
    assert m.idf("khong_co") == pytest.approx(2.0794, abs=1e-4)         # ln 8
    assert m.diem(["ph", "loi"]) == pytest.approx([0.6937, 0.5732, 0.7674], abs=1e-4)
    assert m.diem(["ph", "ph", "loi"]) == pytest.approx(m.diem(["ph", "loi"]))   # từ lặp tính một lần
    assert b.BM25(k1=1.2, b=0.0).fit(DOCS).diem(["ph"]) == pytest.approx([0.6463, 0.0, 0.47], abs=1e-4)


def test_bai1_tim():
    m = nap("bai1_bm25").BM25().fit(DOCS)
    assert [i for i, _ in m.tim(["ph", "loi"], k=2)] == [2, 0]
    assert m.tim(["khong_co"]) == []                                      # bỏ đoạn điểm 0
    eq = nap("bai1_bm25").BM25().fit([["a"], ["a"], ["b"]])
    assert [i for i, _ in eq.tim(["a"])] == [0, 1]                         # bằng điểm: chỉ số nhỏ trước


def test_bai1_ma_loi_tren_so_tay():
    b, c = nap("bai1_bm25"), nap("bai2_chia_doan")
    doan = [d for p in sorted(SO_TAY.glob("*.md")) for d in c.chia_doan(c.TaiLieu(p.stem, p.read_text("utf-8")))]
    m = b.BM25().fit([b.tach_tu(d.noi_dung) for d in doan])
    assert "E-31: pin yếu" in doan[m.tim(b.tach_tu("E-31"), k=1)[0][0]].noi_dung


# ---------- Bài 2 ----------

MD = """# Máy đo

Mở đầu ngắn.

## Bước

Đoạn một.

Đoạn hai.

## Trống

## Dài

""" + "x" * 50 + "\n\nĐoạn sau."


def test_bai2_chia_doan():
    c = nap("bai2_chia_doan")
    doan = c.chia_doan(c.TaiLieu("tl", MD), max_ky_tu=30)
    assert [(d.id, d.muc, d.noi_dung) for d in doan] == [
        ("tl#1", "", "Mở đầu ngắn."),
        ("tl#2", "Bước", "Đoạn một.\n\nĐoạn hai."),
        ("tl#3", "Dài", "x" * 50),                                     # dài hơn trần vẫn giữ nguyên
        ("tl#4", "Dài", "Đoạn sau."),
    ]
    assert {d.tieu_de for d in doan} == {"Máy đo"}
    assert [d.noi_dung for d in c.chia_doan(c.TaiLieu("tl", MD), max_ky_tu=10)][1:3] == ["Đoạn một.", "Đoạn hai."]


def test_bai2_so_tay_va_ngu_canh():
    c = nap("bai2_chia_doan")
    tl = c.TaiLieu("01_hieu_chuan_ph", (SO_TAY / "01_hieu_chuan_ph.md").read_text("utf-8"))
    doan = c.chia_doan(tl)
    tan_suat = next(d for d in doan if d.muc == "Tần suất")
    assert tan_suat.id == "01_hieu_chuan_ph#4" and "#" not in tan_suat.noi_dung
    assert c.them_ngu_canh(tan_suat).startswith("Tài liệu: Hiệu chuẩn máy đo pH. Mục: Tần suất.\nThực hiện lại")
    assert c.them_ngu_canh(doan[0]).startswith("Tài liệu: Hiệu chuẩn máy đo pH.\nÁp dụng")


def test_bai2_yeu_cau_ngu_canh():
    c = nap("bai2_chia_doan")
    tl = c.TaiLieu("tl", MD)
    d = c.chia_doan(tl)[1]
    p = c.yeu_cau_ngu_canh(tl, d)
    check_request({"model": "claude-haiku-5-5", **p})
    text = p["messages"][-1]["content"]
    text = text if isinstance(text, str) else " ".join(b.get("text", "") for b in text)
    assert text.index("<document>") < text.index("Mở đầu ngắn.") < text.index("</document>") < text.index("<chunk>")
    assert "Đoạn một." in text.split("<chunk>")[1]
    assert p["max_tokens"] <= 256 and p["output_config"]["effort"] == "low"
    client, _ = tao_client()
    assert client.create(**p).stop_reason == "end_turn"


# ---------- Bài 3 ----------

def test_bai3_rrf():
    h = nap("bai3_hop_nhat").hop_nhat_rrf
    kq = h(["a", "b", "c"], ["c", "a", "d"], k=1)
    assert [i for i, _ in kq] == ["a", "c", "b", "d"]
    assert dict(kq)["a"] == pytest.approx(1 / 2 + 1 / 3)
    assert dict(kq)["d"] == pytest.approx(1 / 4)
    assert [i for i, _ in h(["x", "y"], ["y", "x"])] == ["x", "y"]          # bằng điểm: xuất hiện trước
    assert h() == []


def test_bai3_khoi_ket_qua_hop_le():
    b3, c = nap("bai3_hop_nhat"), nap("bai2_chia_doan")
    doan = c.chia_doan(c.TaiLieu("tl", MD), max_ky_tu=30)
    khoi = b3.khoi_ket_qua(doan[:2])
    check_request({"model": "claude-haiku-5-5", "messages": [{"role": "user", "content": [*khoi, {"type": "text",
                                                                                                    "text": "?"}]}]})
    assert khoi[0]["title"] == "Máy đo" and khoi[1]["title"] == "Máy đo — Bước"
    assert khoi[1]["source"] == "kb://so-tay/tl#2"
    assert [b["text"] for b in khoi[1]["content"]] == ["Đoạn một.", "Đoạn hai."]
    assert khoi[1]["citations"] == {"enabled": True}
    assert b3.khoi_ket_qua(doan[:1], citations=False)[0]["citations"] == {"enabled": False}


def test_bai3_qua_mock():
    b3, c = nap("bai3_hop_nhat"), nap("bai2_chia_doan")
    tl = c.TaiLieu("02_ma_loi_md300", (SO_TAY / "02_ma_loi_md300.md").read_text("utf-8"))
    client, _ = tao_client()
    msg = client.create(messages=[{"role": "user", "content": [
        *b3.khoi_ket_qua(c.chia_doan(tl)), {"type": "text", "text": "E-22 là lỗi gì?"}]}])
    nguon = b3.nguon_trich_dan(msg)
    assert nguon[0]["source"] == "kb://so-tay/02_ma_loi_md300#3" and nguon[0]["cited_text"].startswith("E-22")


def _msg(blocks, stop="end_turn"):
    return Message.model_validate({"id": "m", "type": "message", "role": "assistant", "model": "claude-haiku-5-5",
                                   "content": blocks, "stop_reason": stop, "stop_sequence": None,
                                   "usage": {"input_tokens": 1, "output_tokens": 1}})


def _cit(source, text, title="T"):
    return {"type": "search_result_location", "cited_text": text, "source": source, "title": title,
            "search_result_index": 0, "start_block_index": 0, "end_block_index": 1}


def test_bai3_nguon_trich_dan():
    b3 = nap("bai3_hop_nhat")
    msg = _msg([{"type": "thinking", "thinking": "", "signature": "s"},
                {"type": "text", "text": "A", "citations": [_cit("kb://1", "x"), _cit("kb://2", "y", None)]},
                {"type": "text", "text": "B", "citations": [_cit("kb://1", "x")]},
                {"type": "text", "text": "C", "citations": [{"type": "char_location", "cited_text": "z",
                 "document_index": 0, "document_title": None, "start_char_index": 0, "end_char_index": 1}]}])
    assert b3.nguon_trich_dan(msg) == [{"source": "kb://1", "title": "T", "cited_text": "x"},
                                       {"source": "kb://2", "title": "", "cited_text": "y"}]
    with pytest.raises(ValueError):
        b3.nguon_trich_dan(_msg([{"type": "text", "text": "A"}], "max_tokens"))
