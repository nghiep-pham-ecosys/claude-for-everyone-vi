"""Chấm tự động bài tập module 01, chạy ở mock mode (không gọi mạng).

    uv run pytest modules/01-messages-api -q                     # chấm lời giải (CI)
    CHAM=exercises uv run pytest modules/01-messages-api -q      # chấm bài của bạn
"""
from pathlib import Path

import anthropic
import pytest
from anthropic.types import Message

from claude_vi import ModelRuleError, estimate_cost_usd
from claude_vi.cham import nap as _nap
from claude_vi.cham import tao_client as _tao_client

MODULE = Path(__file__).resolve().parents[1]


def nap(ten: str):
    return _nap(MODULE, ten)


def tao_client(errors=None):
    return _tao_client(errors=errors)


def message(stop_reason="end_turn", output=18, thinking=6, model="claude-haiku-5-5"):
    usage = {"input_tokens": 12, "output_tokens": output}
    if thinking is not None:
        usage["output_tokens_details"] = {"thinking_tokens": thinking}
    return Message.model_validate({
        "id": "msg_t", "type": "message", "role": "assistant", "model": model,
        "content": [{"type": "text", "text": "ok"}], "stop_reason": stop_reason,
        "stop_sequence": None, "usage": usage,
    })


# ---------- Bài 1 ----------

def test_bai1_gui_tra_ve_text():
    client, _ = tao_client()
    ht = nap("bai1_hoi_thoai").HoiThoai(client)
    assert ht.gui("Xin chào").startswith("[MOCK]")


def test_bai1_lich_su_va_system():
    client, mock = tao_client()
    ht = nap("bai1_hoi_thoai").HoiThoai(client, system="Trả lời ngắn.")
    ht.gui("Câu 1")
    ht.gui("Câu 2")

    lan1, lan2 = mock.da_gui
    assert lan2["system"] == "Trả lời ngắn."
    assert all(m["role"] != "system" for m in lan2["messages"])
    assert [m["role"] for m in lan2["messages"]] == ["user", "assistant", "user"]
    assert lan2["messages"][:1] == lan1["messages"]          # append-only
    assert len(lan1["messages"]) == 1                          # request cũ không bị sửa theo
    assert [m["role"] for m in ht.lich_su] == ["user", "assistant", "user", "assistant"]


def test_bai1_giu_nguyen_block_thinking():
    client, mock = tao_client()
    ht = nap("bai1_hoi_thoai").HoiThoai(client)
    ht.gui("Câu 1")
    ht.gui("Câu 2")
    assistant = mock.da_gui[1]["messages"][1]["content"]
    assert [b.type for b in assistant] == ["thinking", "text"]
    assert assistant[0].signature == "mock-signature"


# ---------- Bài 2 ----------

@pytest.mark.parametrize("reason,expected", [
    ("end_turn", "dung_ket_qua"),
    ("stop_sequence", "dung_ket_qua"),
    ("max_tokens", "tang_max_tokens"),
    ("model_context_window_exceeded", "rut_gon_lich_su"),
    ("tool_use", "chay_tool"),
    ("pause_turn", "gui_lai_nguyen_ven"),
    ("refusal", "doi_model_hoac_dien_dat_lai"),
])
def test_bai2_nen_lam_gi(reason, expected):
    assert nap("bai2_stop_reason").nen_lam_gi(message(stop_reason=reason)) == expected


def test_bai2_stop_reason_la_bao_loi():
    msg = message().model_copy(update={"stop_reason": "ly_do_moi"})
    with pytest.raises(ValueError):
        nap("bai2_stop_reason").nen_lam_gi(msg)


def test_bai2_chi_phi_hoi_thoai():
    msgs = [message(output=18, thinking=6), message(output=100, thinking=None)]
    tong = nap("bai2_stop_reason").chi_phi_hoi_thoai(msgs)
    assert tong["input_tokens"] == 24
    assert tong["output_tokens"] == 118
    assert tong["thinking_tokens"] == 6
    assert tong["usd"] == pytest.approx(sum(estimate_cost_usd(m) for m in msgs))


# ---------- Bài 3 ----------

def test_bai3_tinh_cho():
    b3 = nap("bai3_retry")
    assert b3.tinh_cho(0, rand=lambda: 1.0) == pytest.approx(0.5)
    assert b3.tinh_cho(2, rand=lambda: 1.0) == pytest.approx(2.0)
    assert b3.tinh_cho(2, rand=lambda: 0.0) == pytest.approx(1.0)       # jitter: không dưới 50%
    assert b3.tinh_cho(10, rand=lambda: 1.0) == pytest.approx(8.0)      # có trần
    assert b3.tinh_cho(0, retry_after="3") == pytest.approx(3.0)
    assert b3.tinh_cho(0, retry_after="không-phải-số", rand=lambda: 1.0) == pytest.approx(0.5)


def test_bai3_thu_lai_roi_thanh_cong():
    b3 = nap("bai3_retry")
    client, mock = tao_client(errors=[529, 429])
    cho = []
    msg = b3.goi_co_retry(lambda: client.ask("x"), sleep=cho.append, rand=lambda: 1.0)
    assert msg.stop_reason == "end_turn"
    assert mock.messages.calls == 3
    assert cho == [pytest.approx(0.5), pytest.approx(1.0)]               # lần 2 theo retry-after=1


def test_bai3_het_luot_thi_nem_loi():
    b3 = nap("bai3_retry")
    client, mock = tao_client(errors=[529] * 10)
    cho = []
    with pytest.raises(anthropic.OverloadedError):
        b3.goi_co_retry(lambda: client.ask("x"), max_retries=3, sleep=cho.append)
    assert mock.messages.calls == 4 and len(cho) == 3


@pytest.mark.parametrize("loi", [400, "rule"])
def test_bai3_khong_thu_lai_loi_cua_request(loi):
    b3 = nap("bai3_retry")
    client, _ = tao_client(errors=[400] if loi == 400 else None)
    cho = []
    if loi == 400:
        fn, exc = (lambda: client.ask("x")), anthropic.BadRequestError
    else:
        fn, exc = (lambda: client.ask("x", model="claude-opus-5-5", thinking={"type": "disabled"})), ModelRuleError
    with pytest.raises(exc):
        b3.goi_co_retry(fn, sleep=cho.append)
    assert cho == []
