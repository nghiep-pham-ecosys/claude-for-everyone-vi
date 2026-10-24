"""Chấm tự động bài tập module 02 (mock mode, không gọi mạng).

    uv run pytest modules/02-prompt-engineering -q                    # chấm lời giải
    CHAM=exercises uv run pytest modules/02-prompt-engineering -q     # chấm bài của bạn
"""
import json
import re
from pathlib import Path

import pytest
from anthropic.types import Message

from claude_vi import check_request
from claude_vi.cham import nap as _nap
from claude_vi.cham import tao_client

MODULE = Path(__file__).resolve().parents[1]
NHAN = ["tot", "trung_binh", "xau"]


def nap(ten: str):
    return _nap(MODULE, ten)


def message(text: str, stop_reason: str = "end_turn") -> Message:
    return Message.model_validate({
        "id": "msg_t", "type": "message", "role": "assistant", "model": "claude-haiku-5-5",
        "content": [{"type": "thinking", "thinking": "", "signature": "s"}, {"type": "text", "text": text}],
        "stop_reason": stop_reason, "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 1},
    })


# ---------- Bài 1 ----------

def test_bai1_cau_truc_va_thu_tu():
    p = nap("bai1_tai_lieu").tao_prompt_tai_lieu(
        [("a.txt", "Nội dung A"), ("b.txt", "Nội dung B")], "So sánh A và B?")
    assert p.startswith("<documents>")
    assert p.rstrip().endswith("</question>")
    assert p.index("</documents>") < p.index("<question>")                # tài liệu trước, câu hỏi cuối
    assert re.findall(r'<document index="(\d+)">', p) == ["1", "2"]
    assert p.index("<source>a.txt</source>") < p.index("Nội dung A") < p.index("<source>b.txt</source>")
    assert "So sánh A và B?" in p.split("<question>")[1]


def test_bai1_rong_bao_loi():
    with pytest.raises(ValueError):
        nap("bai1_tai_lieu").tao_prompt_tai_lieu([], "?")


# ---------- Bài 2 ----------

def test_bai2_khoi_vi_du():
    vi_du = [("a", "x"), ("b", "y"), ("c", "x")]
    k = nap("bai2_vi_du").tao_khoi_vi_du(vi_du)
    assert k.startswith("<examples>") and k.rstrip().endswith("</examples>")
    assert k.count("<example>") == 3 and k.count("</example>") == 3
    assert re.findall(r"<input>(.*?)</input>\s*<output>(.*?)</output>", k) == vi_du


@pytest.mark.parametrize("vi_du", [
    [("a", "x"), ("b", "y")],                                   # quá ít
    [(str(i), "x" if i % 2 else "y") for i in range(6)],         # quá nhiều
    [("a", "x"), ("b", "x"), ("c", "x")],                        # không đa dạng
])
def test_bai2_bao_loi(vi_du):
    with pytest.raises(ValueError):
        nap("bai2_vi_du").tao_khoi_vi_du(vi_du)


# ---------- Bài 3 ----------

def test_bai3_yeu_cau_hop_le_va_khong_dung_cach_cu():
    params = nap("bai3_phan_loai").yeu_cau_phan_loai("Sản phẩm dùng tốt.", NHAN)
    check_request({"model": "claude-haiku-5-5", **params})               # không lỗi 400
    schema = params["output_config"]["format"]["schema"]
    assert schema["properties"]["nhan"]["enum"] == NHAN
    assert set(schema["required"]) == {"nhan", "ly_do"}
    assert params["messages"][-1]["role"] == "user"                       # không prefill
    assert "<van_ban>Sản phẩm dùng tốt.</van_ban>" in json.dumps(params["messages"], ensure_ascii=False)
    assert all(n in params["system"] for n in NHAN)


def test_bai3_chay_qua_mock():
    b3 = nap("bai3_phan_loai")
    client, _ = tao_client()
    msg = client.create(**b3.yeu_cau_phan_loai("Sản phẩm dùng tốt.", NHAN))
    assert b3.doc_phan_loai(msg, NHAN) == {"nhan": "tot", "ly_do": "[MOCK]"}


def test_bai3_chuan_hoa_hoa_thuong():
    b3 = nap("bai3_phan_loai")
    data = b3.doc_phan_loai(message('{"nhan": "Trung_Binh", "ly_do": "ok"}'), NHAN)
    assert data["nhan"] == "trung_binh"


@pytest.mark.parametrize("text,stop", [
    ('{"nhan": "to', "max_tokens"),
    ('{"nhan": "tot", "ly_do": ""}', "refusal"),
    ('{"nhan": "tuyet_voi", "ly_do": "?"}', "end_turn"),
])
def test_bai3_bao_loi(text, stop):
    with pytest.raises(ValueError):
        nap("bai3_phan_loai").doc_phan_loai(message(text, stop), NHAN)
