"""Chấm tự động bài tập module 08 (mock mode, không gọi mạng).

    uv run pytest modules/08-agents-workflows -q                    # chấm lời giải (CI)
    CHAM=exercises uv run pytest modules/08-agents-workflows -q     # chấm bài của bạn
"""
import copy
import json
from pathlib import Path

import pytest
from anthropic.types import Message
from claude_vi import estimate_cost_usd, load_models
from claude_vi.cham import nap as _nap
from claude_vi.cham import tao_client

MODULE = Path(__file__).resolve().parents[1]


def nap(ten: str):
    return _nap(MODULE, ten)


def message(text="", stop_reason="end_turn", content=None):
    """Message dựng tay (CONTRIBUTING cho phép trong test) cho nhánh mà mock không tạo ra."""
    return Message.model_validate({
        "id": "msg_t", "type": "message", "role": "assistant", "model": "claude-haiku-5-5",
        "content": content if content is not None else [{"type": "text", "text": text}],
        "stop_reason": stop_reason, "stop_sequence": None,
        "usage": {"input_tokens": 10, "output_tokens": 20},
    })


class ClientGia:
    """Bọc client mock: các lời gọi đầu trả Message dựng sẵn, sau đó chuyển cho mock. Ghi mọi request."""

    def __init__(self, tra_truoc=(), **mock_kwargs):
        self._client, self.mock = tao_client(**mock_kwargs)
        self.settings = self._client.settings
        self._tra_truoc = list(tra_truoc)
        self.da_gui = []

    def create(self, **params):
        self.da_gui.append(copy.deepcopy(params))
        return self._tra_truoc.pop(0) if self._tra_truoc else self._client.create(**params)

    def ask(self, prompt, system=None, **params):
        if system:
            params["system"] = system
        return self.create(messages=[{"role": "user", "content": prompt}], **params)


# ---------- Bài 1 ----------

HOP_LE = {"dai_luong": "do_doc_dien_cuc", "gia_tri": 98.6, "don_vi": "%"}


def test_bai1_cong_qua():
    b1 = nap("bai1_chuoi_co_cong")
    assert b1.kiem_cong(HOP_LE) is None
    assert b1.kiem_cong({"dai_luong": "pH", "gia_tri": 7, "don_vi": ""}) is None      # int cũng là số


@pytest.mark.parametrize("du_lieu", [
    "không phải dict",
    {"dai_luong": "pH", "gia_tri": 7.0},                                             # thiếu don_vi
    {"dai_luong": "do_man", "gia_tri": 7.0, "don_vi": ""},                           # đại lượng lạ
    {"dai_luong": "pH", "gia_tri": "7", "don_vi": ""},                               # chuỗi, không phải số
    {"dai_luong": "pH", "gia_tri": True, "don_vi": ""},                              # bool không phải số
    {"dai_luong": "do_doc_dien_cuc", "gia_tri": 98.6, "don_vi": "[MOCK]"},           # sai đơn vị
    {"dai_luong": "nhiet_do_c", "gia_tri": 75.0, "don_vi": "°C"},                    # ngoài khoảng
    {"dai_luong": "do_doc_dien_cuc", "gia_tri": 0.0, "don_vi": "%"},                 # ngoài khoảng
])
def test_bai1_cong_chan_du_lieu_sai(du_lieu):
    ly_do = nap("bai1_chuoi_co_cong").kiem_cong(du_lieu)
    assert isinstance(ly_do, str) and ly_do


def test_bai1_cong_truot_thi_khong_goi_buoc_2():
    b1 = nap("bai1_chuoi_co_cong")
    client, mock = tao_client()
    kq = b1.chuoi_hai_buoc(client, "Độ dốc điện cực đo được 98,6 %.")
    assert mock.messages.calls == 1                       # mock trả don_vi "[MOCK]": cổng trượt
    assert kq["ok"] is False and kq["ly_do"] and kq["tom_tat"] is None
    assert isinstance(kq["phep_do"], dict)
    fmt = mock.da_gui[0]["output_config"]["format"]
    assert fmt == {"type": "json_schema", "schema": b1.SCHEMA}
    assert "98,6" in json.dumps(mock.da_gui[0]["messages"], ensure_ascii=False)


def test_bai1_cong_qua_thi_goi_buoc_2():
    b1 = nap("bai1_chuoi_co_cong")
    client = ClientGia([message(json.dumps(HOP_LE))])
    kq = b1.chuoi_hai_buoc(client, "Độ dốc điện cực đo được 98,6 %.")
    assert len(client.da_gui) == 2
    assert kq == {"ok": True, "ly_do": None, "phep_do": HOP_LE, "tom_tat": kq["tom_tat"]}
    assert kq["tom_tat"].startswith("[MOCK]")


@pytest.mark.parametrize("buoc1", [message("{khong phai json"), message("", stop_reason="max_tokens")])
def test_bai1_buoc_1_hong_thi_dung(buoc1):
    client = ClientGia([buoc1])
    kq = nap("bai1_chuoi_co_cong").chuoi_hai_buoc(client, "pH 7,1.")
    assert len(client.da_gui) == 1
    assert kq["ok"] is False and kq["ly_do"]


# ---------- Bài 2 ----------

def _xu_ly(goi):
    def tao(nhan):
        def ham(cau_hoi):
            goi.append(nhan)
            return f"xử lý {nhan}"
        return ham
    return {n: tao(n) for n in ("quy_trinh", "so_lieu", "khac")}, tao("du_phong")


@pytest.mark.parametrize("cau_hoi,nhan", [
    ("Quy trình hiệu chuẩn máy đo pH gồm những bước nào?", "quy_trinh"),
    ("Số liệu AQI ở Hà Nội lúc này là bao nhiêu?", "so_lieu"),
    ("Trưa nay nên ăn món gì?", "khac"),
])
def test_bai2_moi_nhan_toi_dung_ham(cau_hoi, nhan):
    b2 = nap("bai2_dinh_tuyen")
    client, mock = tao_client()
    goi = []
    xu_ly, du_phong = _xu_ly(goi)
    assert b2.dinh_tuyen(client, cau_hoi, xu_ly, du_phong) == (nhan, f"xử lý {nhan}")
    assert goi == [nhan] and mock.messages.calls == 1
    req = mock.da_gui[0]
    assert req["output_config"]["format"]["schema"] == b2.SCHEMA
    assert req["messages"] == [{"role": "user", "content": cau_hoi}]


@pytest.mark.parametrize("tra_ve", [
    message(json.dumps({"nhan": "thoi_tiet"})),            # nhãn lạ
    message("{hỏng"),                                      # JSON hỏng
    message(json.dumps({"loai": "so_lieu"})),              # thiếu khoá
    message("", stop_reason="refusal"),
])
def test_bai2_nhan_la_vao_du_phong(tra_ve):
    goi = []
    xu_ly, du_phong = _xu_ly(goi)
    client = ClientGia([tra_ve])
    assert nap("bai2_dinh_tuyen").dinh_tuyen(client, "x", xu_ly, du_phong) == ("du_phong", "xử lý du_phong")
    assert goi == ["du_phong"] and len(client.da_gui) == 1


def test_bai2_nhan_hop_le_nhung_chua_co_ham():
    client, _ = tao_client()
    goi = []
    xu_ly, du_phong = _xu_ly(goi)
    del xu_ly["khac"]
    assert nap("bai2_dinh_tuyen").dinh_tuyen(client, "Trưa nay nên ăn món gì?", xu_ly, du_phong)[0] == "du_phong"


# ---------- Bài 3 ----------

def _tool(name, props):
    return {"name": name, "description": f"Tool mẫu {name} (dữ liệu bịa).", "input_schema": {
        "type": "object", "properties": props, "required": list(props), "additionalProperties": False}}


DOC = _tool("doc_so_tay", {"trang": {"type": "string", "enum": ["hieu_chuan", "an_toan"]}})
AQI = _tool("tra_aqi", {"thanh_pho": {"type": "string", "enum": ["Hà Nội", "Đà Nẵng"]}})
GHI = _tool("ghi_nhat_ky", {"noi_dung": {"type": "string"}})


def _registry(nhat_ky):
    return {
        "doc_so_tay": lambda trang: f"Trang {trang}: hiệu chuẩn sau mỗi 8 giờ.",
        "tra_aqi": lambda thanh_pho: {"thanh_pho": thanh_pho, "aqi": 152},
        "ghi_nhat_ky": lambda noi_dung: nhat_ky.append(noi_dung) or "đã ghi",
    }


def _ket_qua_tool(da_gui):
    """Mọi tool_result trong request cuối, theo thứ tự."""
    return [b for m in da_gui[-1]["messages"] if isinstance(m["content"], list)
            for b in m["content"] if isinstance(b, dict) and b.get("type") == "tool_result"]


def _chay(b3, client, duyet=lambda ten, inp: True, tools=(DOC, AQI, GHI), registry=None, **kw):
    nhat_ky, trace = [], []
    kq = b3.chay_agent(client, "Chuẩn bị ca đo", list(tools), registry or _registry(nhat_ky), duyet,
                       trace=trace, **kw)
    return kq, nhat_ky, trace


def test_bai3_chay_toi_end_turn():
    b3 = nap("bai3_agent_an_toan")
    client, mock = tao_client(multi_step=True)            # mock gọi từng tool một, rồi trả lời
    kq, nhat_ky, trace = _chay(b3, client)
    assert kq["ly_do_dung"] == "end_turn" and kq["so_loi_goi"] == 4 == mock.messages.calls
    assert nhat_ky == ["[MOCK]"]
    assert kq["msg"].stop_reason == "end_turn"
    assert [t["tools"] for t in trace] == [["doc_so_tay"], ["tra_aqi"], ["ghi_nhat_ky"], []]
    assert [t["luot"] for t in trace] == [1, 2, 3, 4]
    assert kq["usd"] == pytest.approx(sum(t["usd"] for t in trace))


def test_bai3_giu_lich_su_append_only_va_thinking():
    b3 = nap("bai3_agent_an_toan")
    client, mock = tao_client(multi_step=True)
    _chay(b3, client)
    lan_truoc = None
    for req in mock.da_gui:
        if lan_truoc is not None:
            assert req["messages"][:len(lan_truoc)] == lan_truoc       # chỉ nối thêm
        lan_truoc = req["messages"]
    assistant = mock.da_gui[1]["messages"][1]["content"]
    assert assistant[0].type == "thinking"


def test_bai3_dung_o_tran_luot():
    b3 = nap("bai3_agent_an_toan")
    client, mock = tao_client(multi_step=True)
    kq, _, trace = _chay(b3, client, toi_da_luot=2)
    assert kq["ly_do_dung"] == "het_luot" and kq["so_loi_goi"] == 2 == mock.messages.calls == len(trace)


def test_bai3_dung_o_tran_chi_phi():
    b3 = nap("bai3_agent_an_toan")
    client, mock = tao_client(multi_step=True)
    gia = load_models()["models"][client.settings.model]["price_per_mtok"]["output"]
    tran_1 = client.settings.max_tokens * gia / 1_000_000
    kq, _, _ = _chay(b3, client, tran_usd=tran_1 * 1.01)       # đủ cho đúng một lời gọi
    assert kq["ly_do_dung"] == "tran_chi_phi" and kq["so_loi_goi"] == 1 == mock.messages.calls
    assert kq["usd"] <= tran_1 * 1.01


def test_bai3_tran_qua_nho_thi_khong_goi():
    b3 = nap("bai3_agent_an_toan")
    client, mock = tao_client(multi_step=True)
    kq, _, trace = _chay(b3, client, tran_usd=0.0)
    assert kq["ly_do_dung"] == "tran_chi_phi" and mock.messages.calls == 0 and trace == []
    assert kq["msg"] is None and kq["usd"] == 0


def test_bai3_chua_duyet_thi_is_error_va_khong_chay():
    b3 = nap("bai3_agent_an_toan")
    client, mock = tao_client(multi_step=True)
    hoi = []

    def duyet(ten, inp):
        hoi.append((ten, inp))
        return False

    kq, nhat_ky, _ = _chay(b3, client, duyet=duyet)
    assert nhat_ky == [] and hoi == [("ghi_nhat_ky", {"noi_dung": "[MOCK]"})]   # chỉ tool can_duyet mới hỏi
    ket_qua = _ket_qua_tool(mock.da_gui)
    assert [bool(r.get("is_error")) for r in ket_qua] == [False, False, True]
    assert ket_qua[1]["content"] == json.dumps({"thanh_pho": "Hà Nội", "aqi": 152}, ensure_ascii=False)
    assert kq["ly_do_dung"] == "end_turn"                      # Claude nhận lỗi rồi trả lời tiếp


def test_bai3_tool_khong_co_trong_registry():
    b3 = nap("bai3_agent_an_toan")
    client, mock = tao_client(multi_step=True)
    reg = _registry([])
    del reg["tra_aqi"]
    _chay(b3, client, registry=reg)
    loi = _ket_qua_tool(mock.da_gui)[1]
    assert loi["is_error"] is True and "doc_so_tay" in loi["content"]


def test_bai3_tool_nem_loi():
    b3 = nap("bai3_agent_an_toan")
    client, mock = tao_client(multi_step=True)

    def hong(trang):
        raise ConnectionError("máy chủ sổ tay không phản hồi")

    _chay(b3, client, tools=(DOC,), registry={"doc_so_tay": hong})
    loi = _ket_qua_tool(mock.da_gui)[0]
    assert loi["is_error"] is True and loi["content"] == "ConnectionError: máy chủ sổ tay không phản hồi"


def test_bai3_dung_khi_max_tokens():
    b3 = nap("bai3_agent_an_toan")
    client = ClientGia([message("", stop_reason="max_tokens", content=[])], multi_step=True)
    kq, _, trace = _chay(b3, client)
    assert kq["ly_do_dung"] == "max_tokens" and kq["so_loi_goi"] == 1 and len(trace) == 1
    assert kq["usd"] == pytest.approx(estimate_cost_usd(kq["msg"]))


def test_bai3_trace_ghi_duoc_json():
    b3 = nap("bai3_agent_an_toan")
    client, _ = tao_client(multi_step=True)
    _, _, trace = _chay(b3, client)
    for dong in trace:
        assert set(dong) == {"luot", "stop_reason", "tools", "input_tokens", "output_tokens", "usd"}
        json.dumps(dong)
