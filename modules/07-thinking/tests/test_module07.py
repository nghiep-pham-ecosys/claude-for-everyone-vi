"""Chấm tự động bài tập module 07 (mock mode, không gọi mạng).

    uv run pytest modules/07-thinking -q                    # chấm lời giải
    CHAM=exercises uv run pytest modules/07-thinking -q     # chấm bài của bạn
"""
from pathlib import Path

import anthropic
import pytest
from anthropic.types import Message
from claude_vi import ClaudeVi, check_request, load_models
from claude_vi.cham import SETTINGS, tao_client
from claude_vi.cham import nap as _nap
from claude_vi.mock import MockAnthropic

MODULE = Path(__file__).resolve().parents[1]
ACTIVE = [m for m, e in load_models()["models"].items() if e.get("status") == "active"]


def nap(ten: str):
    return _nap(MODULE, ten)


def message(blocks, stop_reason="end_turn", output=100, thinking=60):
    details = {"thinking_tokens": thinking} if thinking is not None else None
    return Message.model_validate({
        "id": "msg_t", "type": "message", "role": "assistant", "model": "claude-haiku-5-5", "content": blocks,
        "stop_reason": stop_reason, "stop_sequence": None,
        "usage": {"input_tokens": 1, "output_tokens": output, "output_tokens_details": details},
    })


def th(text=""):
    return {"type": "thinking", "thinking": text, "signature": "s"}


def tx(text):
    return {"type": "text", "text": text}


# ---------- Bài 1 ----------

@pytest.mark.parametrize("model", ACTIVE)
def test_bai1_it_thinking_nhat_hop_le_moi_model(model):
    params = nap("bai1_cau_hinh").it_thinking_nhat(model)
    check_request({"model": model, "messages": [{"role": "user", "content": "x"}], **params})
    assert params["output_config"] == {"effort": "low"}
    rules = load_models()["models"][model]["rules"]
    loai = (params.get("thinking") or {}).get("type")
    if rules["thinking_disabled_allowed"]:
        assert loai == "disabled"
    elif rules["between_tools_allowed"]:
        assert loai == "between_tools"
    else:
        assert "thinking" not in params


def test_bai1_dung_luat_tung_model():
    b1 = nap("bai1_cau_hinh")
    assert b1.it_thinking_nhat("claude-haiku-5-5")["thinking"] == {"type": "disabled"}
    assert b1.it_thinking_nhat("claude-sonnet-5-5")["thinking"] == {"type": "between_tools"}
    assert "thinking" not in b1.it_thinking_nhat("claude-opus-5-5")


@pytest.mark.parametrize("model", ACTIVE)
def test_bai1_xem_tom_tat(model):
    b1 = nap("bai1_cau_hinh")
    p = b1.xem_tom_tat(model)
    assert p == {"thinking": {"type": "adaptive", "display": "summarized"}}
    p = b1.xem_tom_tat(model, "high")
    check_request({"model": model, "messages": [{"role": "user", "content": "x"}], **p})
    assert p["output_config"] == {"effort": "high"}


@pytest.mark.parametrize("model", ["claude-3-haiku-20240307", "claude-sonnet-4-5-20250929", "khong-co"])
def test_bai1_model_khong_active(model):
    b1 = nap("bai1_cau_hinh")
    with pytest.raises(ValueError):
        b1.it_thinking_nhat(model)
    with pytest.raises(ValueError):
        b1.xem_tom_tat(model)


# ---------- Bài 2 ----------

def test_bai2_bao_cao():
    b2 = nap("bai2_bao_cao")
    msg = message([th("Bước 1."), {"type": "redacted_thinking", "data": "x"}, th(""), th("Bước 2."), tx("Đáp án")])
    r = b2.bao_cao(msg)
    assert (r.khoi_thinking, r.khoi_redacted) == (3, 1)
    assert r.tom_tat == "Bước 1.\nBước 2."
    assert (r.thinking_tokens, r.text_tokens, r.ty_le_thinking) == (60, 40, 0.6)


def test_bai2_bao_cao_thieu_so_lieu():
    b2 = nap("bai2_bao_cao")
    r = b2.bao_cao(message([tx("a")], output=0, thinking=None))
    assert (r.khoi_thinking, r.tom_tat, r.thinking_tokens, r.text_tokens, r.ty_le_thinking) == (0, "", 0, 0, 0.0)


def test_bai2_qua_mock():
    b2 = nap("bai2_bao_cao")
    client, _ = tao_client()
    an = b2.bao_cao(client.ask("x"))
    hien = b2.bao_cao(client.ask("x", thinking={"type": "adaptive", "display": "summarized"}))
    assert an.tom_tat == "" and hien.tom_tat.startswith("[MOCK]")
    assert an.thinking_tokens == hien.thinking_tokens > 0                    # hiện hay ẩn đều tính như nhau
    assert b2.chan_doan(client.ask("x", max_tokens=6)) == "thinking_dung_het_max_tokens"


@pytest.mark.parametrize("blocks,stop,ket_qua", [
    ([th(), tx("xong")], "end_turn", "ok"),
    ([th(), tx("xong")], "tool_use", "ok"),
    ([th()], "max_tokens", "thinking_dung_het_max_tokens"),
    ([th(), tx("  ")], "max_tokens", "thinking_dung_het_max_tokens"),
    ([th(), tx("Đang giải thích")], "max_tokens", "bi_cat_ngang"),
    ([tx("Xin lỗi")], "refusal", "tu_choi"),
    ([th(), tx("...")], "model_context_window_exceeded", "het_context"),
])
def test_bai2_chan_doan(blocks, stop, ket_qua):
    assert nap("bai2_bao_cao").chan_doan(message(blocks, stop)) == ket_qua


# ---------- Bài 3 ----------

def test_bai3_hoi_thoai_append_only():
    b3 = nap("bai3_append_only")
    client, mock = tao_client()
    ht = b3.HoiThoai(client, "Trả lời ngắn.")
    assert ht.gui("Câu 1").startswith("[MOCK]")
    ht.them_chi_dan("Từ giờ trả lời bằng tiếng Anh.")
    ht.them_chi_dan("Không dùng markdown.")
    ht.gui("Câu 2")                              # mock trả 400 nếu system hay lượt cũ bị sửa
    ht.gui("Câu 3")
    assert {p["system"] for p in mock.da_gui} == {"Trả lời ngắn."}
    roles = [m["role"] for m in mock.da_gui[2]["messages"]]
    assert roles == ["user", "assistant", "user", "system", "assistant", "user"]
    assert mock.da_gui[2]["messages"][3]["content"] == "Từ giờ trả lời bằng tiếng Anh.\nKhông dùng markdown."
    assert mock.da_gui[1]["messages"][1]["content"][0].type == "thinking"     # gửi lại nguyên vẹn
    assert [m["role"] for m in ht.messages][-1] == "assistant"


def test_bai3_system_chi_doc_va_chi_dan_rong():
    b3 = nap("bai3_append_only")
    client, _ = tao_client()
    ht = b3.HoiThoai(client, "S")
    with pytest.raises(AttributeError):
        ht.system = "S2"
    with pytest.raises(ValueError):
        ht.them_chi_dan("   ")


def test_bai3_luu_va_chay_tiep():
    b3 = nap("bai3_append_only")
    mock = MockAnthropic()
    ht = b3.HoiThoai(ClaudeVi(settings=SETTINGS, client=mock), "S")
    ht.gui("Câu 1")
    phien = ht.luu()
    phien["messages"].append({"role": "user", "content": "chỉ sửa bản sao"})
    assert len(ht.messages) == 2                                              # bản sao sâu
    # phát lại đúng những gì đã gửi: cùng mock (cùng "tài khoản") nên block thinking còn hợp lệ
    tiep = ClaudeVi(settings=SETTINGS, client=mock)
    msg = tiep.create(system=phien["system"], messages=[*phien["messages"][:2], {"role": "user", "content": "Câu 2"}])
    assert msg.stop_reason == "end_turn"
    with pytest.raises(anthropic.BadRequestError, match="different conversation"):
        tiep.create(system="S (dựng lại từ template)", messages=[*ht.messages, {"role": "user", "content": "Câu 2"}])
