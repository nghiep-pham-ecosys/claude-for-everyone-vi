"""Chấm tự động bài tập module 03 (mock mode, không gọi mạng).

    uv run pytest modules/03-tool-use -q                    # chấm lời giải
    CHAM=exercises uv run pytest modules/03-tool-use -q     # chấm bài của bạn
"""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from claude_vi import check_request, text_of
from claude_vi.cham import nap as _nap
from claude_vi.cham import tao_client

MODULE = Path(__file__).resolve().parents[1]

MO_TA = ("Tra nhiệt độ hiện tại của một trạm đo. Dùng khi người dùng hỏi nhiệt độ. "
         "Trả về một số thực độ C. Không trả về dự báo.")
THUOC_TINH = {"tram": {"type": "string", "enum": ["T1", "T2"]}, "don_vi": {"type": "string", "enum": ["C", "F"]}}


def nap(ten: str):
    return _nap(MODULE, ten)


def tool_use(name, input, id="toolu_t1"):
    return SimpleNamespace(type="tool_use", id=id, name=name, input=input)


# ---------- Bài 1 ----------

def test_bai1_tool_strict_hop_le():
    tool = nap("bai1_dinh_nghia_tool").tao_tool("tram_tra_nhiet_do", MO_TA, THUOC_TINH, ["tram"])
    assert tool["strict"] is True and tool["name"] == "tram_tra_nhiet_do" and tool["description"] == MO_TA
    s = tool["input_schema"]
    assert s["type"] == "object" and s["properties"] == THUOC_TINH and s["required"] == ["tram"]
    assert s["additionalProperties"] is False
    check_request({"model": "claude-haiku-5-5", "messages": [{"role": "user", "content": "x"}], "tools": [tool]})


@pytest.mark.parametrize("ten,mo_ta,bat_buoc", [
    ("tra nhiệt độ", MO_TA, ["tram"]),               # tên có dấu và khoảng trắng
    ("tram_tra", "Tra nhiệt độ.", ["tram"]),         # mô tả quá ngắn
    ("tram_tra", MO_TA, ["tram", "ngay"]),           # bắt buộc trường không tồn tại
])
def test_bai1_bao_loi(ten, mo_ta, bat_buoc):
    with pytest.raises(ValueError):
        nap("bai1_dinh_nghia_tool").tao_tool(ten, mo_ta, THUOC_TINH, bat_buoc)


# ---------- Bài 2 ----------

def test_bai2_thanh_cong_dict_va_str():
    b2 = nap("bai2_chay_tool")
    reg = {"tra": lambda tram: {"tram": tram, "c": 24.5}, "chao": lambda: "xin chào"}
    r = b2.chay_tool(tool_use("tra", {"tram": "T1"}), reg)
    assert r["type"] == "tool_result" and r["tool_use_id"] == "toolu_t1"
    assert json.loads(r["content"]) == {"tram": "T1", "c": 24.5} and not r.get("is_error")
    assert b2.chay_tool(tool_use("chao", {}), reg)["content"] == "xin chào"


def test_bai2_tool_khong_ton_tai():
    r = nap("bai2_chay_tool").chay_tool(tool_use("xoa_het", {}), {"tra": print, "ghi": print})
    assert r["is_error"] is True
    assert "xoa_het" in r["content"] and "tra" in r["content"] and "ghi" in r["content"]


def test_bai2_tool_nem_loi():
    def hong(tram):
        raise ValueError(f"trạm {tram} mất kết nối")

    r = nap("bai2_chay_tool").chay_tool(tool_use("tra", {"tram": "T2"}), {"tra": hong})
    assert r["is_error"] is True and r["content"].startswith("ValueError:") and "T2" in r["content"]


# ---------- Bài 3 ----------

TOOLS = [
    {"name": "tra_a", "description": "A.", "strict": True, "input_schema": {
        "type": "object", "properties": {"tram": {"type": "string", "enum": ["T1"]}},
        "required": ["tram"], "additionalProperties": False}},
    {"name": "tra_b", "description": "B.", "strict": True, "input_schema": {
        "type": "object", "properties": {}, "required": [], "additionalProperties": False}},
]
REG = {"tra_a": lambda tram: f"A({tram})", "tra_b": lambda: "B"}


def test_bai3_chay_het_vong_va_song_song():
    client, mock = tao_client()
    msg = nap("bai3_vong_lap").vong_lap(client, "Đo giúp", TOOLS, REG)
    assert msg.stop_reason == "end_turn"
    assert "A(T1)" in text_of(msg) and "B" in text_of(msg)
    assert len(mock.da_gui) == 2
    lan2 = mock.da_gui[1]["messages"]
    assert [m["role"] for m in lan2] == ["user", "assistant", "user"]
    ket_qua = lan2[2]["content"]
    assert [r["type"] for r in ket_qua] == ["tool_result", "tool_result"]       # cả hai trong MỘT lượt
    ids = [b.id for b in lan2[1]["content"] if b.type == "tool_use"]
    assert [r["tool_use_id"] for r in ket_qua] == ids                           # đúng thứ tự


def test_bai3_giu_thinking():
    client, mock = tao_client()
    nap("bai3_vong_lap").vong_lap(client, "Đo giúp", TOOLS, REG)              # mock trả 400 nếu thinking bị bỏ
    assert mock.da_gui[1]["messages"][1]["content"][0].type == "thinking"


def test_bai3_gioi_han_luot():
    client, mock = tao_client()
    with pytest.raises(RuntimeError):
        nap("bai3_vong_lap").vong_lap(client, "Đo giúp", TOOLS, REG, max_luot=1)
    assert len(mock.da_gui) == 1


def test_bai3_khong_tool_thi_tra_ngay():
    client, mock = tao_client()
    msg = nap("bai3_vong_lap").vong_lap(client, "Chào", [], REG)
    assert msg.stop_reason == "end_turn" and len(mock.da_gui) == 1
