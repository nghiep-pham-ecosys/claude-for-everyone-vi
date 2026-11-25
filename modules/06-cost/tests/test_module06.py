"""Kiểm script ước tính chi phí của module 06 (mock mode, không gọi mạng, không cần key).

    uv run pytest modules/06-cost -q
"""
import importlib.util
import math
import sys
from pathlib import Path

import anthropic
import pytest
from anthropic.types import Message
from anthropic.types.messages import MessageBatchIndividualResponse
from claude_vi import check_request, estimate_cost_usd, load_models
from claude_vi.cham import nap as _nap
from claude_vi.cham import tao_client

MODULE = Path(__file__).resolve().parents[1]
MODELS = load_models()["models"]
ACTIVE = [m for m, e in MODELS.items() if e.get("status") == "active"]
KHONG_GIA = [m for m, e in MODELS.items() if not e.get("price_per_mtok")]


def _nap_script():
    path = MODULE / "python" / "01_uoc_tinh_chi_phi.py"
    spec = importlib.util.spec_from_file_location("module06_uoc_tinh_chi_phi", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # chỉ định nghĩa hàm; main() chạy khi gọi trực tiếp
    return mod


S = _nap_script()


@pytest.mark.parametrize("model", ACTIVE)
def test_tran_output_doc_gia_tu_config(model):
    gia = MODELS[model]["price_per_mtok"]
    assert S.gia(model) == gia
    assert S.tran_chi_phi_output(model, 1024) == pytest.approx(1024 * gia["output"] / 1e6)


@pytest.mark.parametrize("model", KHONG_GIA)
def test_model_chua_co_gia_tra_nan(model):
    assert S.gia(model) is None
    assert math.isnan(S.tran_chi_phi_output(model, 1024))


@pytest.mark.parametrize("model", ACTIVE)
@pytest.mark.parametrize("effort", ["low", "high"])
def test_tach_chi_phi_khop_estimate_va_duoi_tran(model, effort):
    client, mock = tao_client()
    max_tokens = 256
    msg = client.ask("x", model=model, max_tokens=max_tokens, output_config={"effort": effort})
    assert mock.messages.calls == 1  # đi qua mock, không qua mạng

    c, gia, u = S.tach_chi_phi(msg), MODELS[model]["price_per_mtok"], msg.usage
    assert c["input"] == pytest.approx(u.input_tokens * gia["input"] / 1e6)
    assert c["output"] == pytest.approx(u.output_tokens * gia["output"] / 1e6)
    assert c["tong"] == pytest.approx(estimate_cost_usd(msg))
    assert 0 < c["thinking"] <= c["output"]  # thinking nằm trong output, không cộng thêm
    assert c["output"] <= S.tran_chi_phi_output(model, max_tokens)
    assert c["token_cache"] == 0


def test_main_chay_mock_khong_can_key(monkeypatch, capsys):
    monkeypatch.setenv("CLAUDE_MOCK", "1")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)

    def cam_goi_that(*a, **k):
        raise AssertionError("script không được tạo client thật")

    monkeypatch.setattr(anthropic, "Anthropic", cam_goi_that)
    S.main()
    out = capsys.readouterr().out
    assert "estimate_cost_usd" in out
    for model in ACTIVE:
        assert model in out


# ---------- Script 02–05 và bài tập (prompt caching, đếm token, batch, message threads) ----------

def _nap_py(ten):
    path = MODULE / "python" / f"{ten}.py"
    spec = importlib.util.spec_from_file_location(f"module06_{ten}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


S2, S3, S4, S5 = (_nap_py(t) for t in ("02_prompt_caching", "03_dem_token", "04_batch", "05_message_threads"))


def nap(ten):
    return _nap(MODULE, ten)


def _cam_goi_that(monkeypatch):
    monkeypatch.setenv("CLAUDE_MOCK", "1")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)

    def cam(*a, **k):
        raise AssertionError("script không được tạo client thật")

    monkeypatch.setattr(anthropic, "Anthropic", cam)


@pytest.mark.parametrize("script", [S2, S3, S4, S5], ids=["02", "03", "04", "05"])
def test_script_chay_mock_khong_can_key(script, monkeypatch, capsys):
    _cam_goi_that(monkeypatch)
    script.main()
    assert capsys.readouterr().out.strip()


def test_s2_ghi_mot_lan_roi_doc():
    client, _ = tao_client()
    tong = client.count_tokens(system=S2.system_co_cache(), messages=[{"role": "user", "content": "a"}]).input_tokens
    assert tong >= MODELS[client.settings.model]["cache_min_tokens"]
    m1 = client.create(system=S2.system_co_cache(), messages=[{"role": "user", "content": "a"}])
    m2 = client.create(system=S2.system_co_cache(), messages=[{"role": "user", "content": "b"}])
    t1, t2 = S2.tach_input(m1), S2.tach_input(m2)
    assert sum(t1.values()) == tong                       # tổng input = đọc + ghi + input
    assert t1["ghi_5m"] > 0 and t1["doc"] == 0
    assert t2["doc"] == t1["ghi_5m"] and t2["ghi_5m"] == 0
    assert estimate_cost_usd(m1) > S2.chi_phi_neu_khong_cache(m1)  # ghi đắt hơn input thường
    assert estimate_cost_usd(m2) < S2.chi_phi_neu_khong_cache(m2)  # đọc rẻ hơn nhiều


def test_s2_ttl_1h_tinh_vao_ephemeral_1h():
    client, _ = tao_client()
    msg = client.create(system=S2.system_co_cache("1h"), messages=[{"role": "user", "content": "a"}])
    t = S2.tach_input(msg)
    assert t["ghi_1h"] > 0 and t["ghi_5m"] == 0
    cache = MODELS[msg.model]["cache_price_per_mtok"]
    u = msg.usage
    assert estimate_cost_usd(msg) == pytest.approx(
        (u.input_tokens * MODELS[msg.model]["price_per_mtok"]["input"] + t["ghi_1h"] * cache["write_1h"]
         + u.output_tokens * MODELS[msg.model]["price_per_mtok"]["output"]) / 1e6)


def test_s2_breakpoint_tren_block_doi_moi_lan_khong_bao_gio_doc():
    client, _ = tao_client()
    for gio in ("08:00", "08:01", "08:02"):
        system = [{"type": "text", "text": S2.SO_TAY},
                  {"type": "text", "text": gio, "cache_control": {"type": "ephemeral"}}]
        msg = client.create(system=system, messages=[{"role": "user", "content": "x"}])
        assert msg.usage.cache_read_input_tokens == 0 and msg.usage.cache_creation_input_tokens > 0


def test_s2_prompt_ngan_khong_cache_khong_loi():
    client, _ = tao_client()
    msg = client.create(system=[{"type": "text", "text": "ngắn", "cache_control": {"type": "ephemeral"}}],
                        messages=[{"role": "user", "content": "x"}])
    assert msg.usage.cache_creation_input_tokens == 0 == msg.usage.cache_read_input_tokens


def test_s2_doi_effort_mat_cache():
    client, _ = tao_client()
    hoi = [{"role": "user", "content": "x"}]
    client.create(system=S2.system_co_cache(), messages=hoi)
    msg = client.create(system=S2.system_co_cache(), messages=hoi, output_config={"effort": "low"})
    assert msg.usage.cache_read_input_tokens == 0 and msg.usage.cache_creation_input_tokens > 0
    mac_dinh = MODELS[client.settings.model]["default_effort"]
    msg = client.create(system=S2.system_co_cache(), messages=hoi, output_config={"effort": mac_dinh})
    assert msg.usage.cache_read_input_tokens > 0  # đặt effort bằng đúng mặc định: không mất cache


@pytest.mark.parametrize("model", ACTIVE)
def test_s2_hoa_von_theo_docs(model):
    # docs Pricing: 5 phút hoà vốn sau 1 lần đọc, 1 giờ sau 2 lần đọc
    assert S2.so_lan_doc_hoa_von(model, "5m") == 1
    assert S2.so_lan_doc_hoa_von(model, "1h") == 2


def test_s3_uoc_tinh_dem_mot_lan_khong_goi_create():
    client, mock = tao_client()
    u = S3.uoc_tinh_truoc(client, {"system": S3.SO_TAY, "messages": [{"role": "user", "content": "x"}],
                                   "max_tokens": 300})
    gia = MODELS[client.settings.model]["price_per_mtok"]
    assert mock.messages.count_calls == 1 and mock.messages.calls == 0
    assert u["tran_output_usd"] == pytest.approx(300 * gia["output"] / 1e6)
    assert u["toi_da_usd"] == pytest.approx(u["input_usd"] + u["tran_output_usd"])


def test_s3_tool_lam_tang_input():
    client, _ = tao_client()
    hoi = [{"role": "user", "content": "x"}]
    assert (client.count_tokens(messages=hoi, tools=[S3.TRA_THIET_BI]).input_tokens
            > client.count_tokens(messages=hoi).input_tokens)


def test_count_tokens_cung_luat_400_voi_create():
    client, _ = tao_client()
    with pytest.raises(ValueError, match="temperature"):
        client.count_tokens(messages=[{"role": "user", "content": "x"}], temperature=0.5)
    with pytest.raises(TypeError):  # count_tokens không có max_tokens
        client._client.messages.count_tokens(model="claude-haiku-5-5", max_tokens=5,
                                             messages=[{"role": "user", "content": "x"}])


def test_s4_batch_ghep_theo_custom_id():
    client, _ = tao_client()
    requests = S4.tao_requests(S4.CAU_HOI)
    assert [r["custom_id"] for r in requests] == [f"cau-{i:03d}" for i in range(len(S4.CAU_HOI))]
    batch = client.batch_create(requests)
    assert batch.processing_status == "in_progress"
    with pytest.raises(anthropic.AnthropicError):
        client.batch_results(batch.id)  # chưa ended thì chưa có kết quả
    batch = S4.cho_xong(client, batch.id, cho_toi_da_s=5, nghi_s=0)
    assert batch.processing_status == "ended" and batch.request_counts.succeeded == len(requests)
    ket_qua = list(client.batch_results(batch.id))
    assert [r.custom_id for r in ket_qua] != [r["custom_id"] for r in requests]  # không theo thứ tự gửi
    gom = S4.gom_ket_qua(ket_qua)
    assert set(gom) == {r["custom_id"] for r in requests}
    for r in ket_qua:
        assert gom[r.custom_id]["usd"] == pytest.approx(estimate_cost_usd(r.result.message) / 2)


def test_s4_batch_huy_khong_tinh_tien():
    client, _ = tao_client()
    batch = client.batch_create(S4.tao_requests(["a", "b"]))
    assert client.batch_cancel(batch.id).processing_status == "canceling"
    batch = client.batch_retrieve(batch.id)
    assert batch.processing_status == "ended" and batch.request_counts.canceled == 2
    gom = S4.gom_ket_qua(client.batch_results(batch.id))
    assert all(v["loai"] == "canceled" and v["usd"] == 0 for v in gom.values())


@pytest.mark.parametrize("custom_id", ["có dấu", "a" * 65, "", "a.b", "ok\n"])
def test_batch_custom_id_sai_bi_tu_choi(custom_id):
    client, _ = tao_client()
    with pytest.raises(anthropic.BadRequestError):
        client.batch_create([{"custom_id": custom_id, "params": {"messages": [{"role": "user", "content": "x"}]}}])


def test_batch_custom_id_trung_bi_tu_choi():
    client, _ = tao_client()
    req = {"custom_id": "a", "params": {"messages": [{"role": "user", "content": "x"}]}}
    with pytest.raises(anthropic.BadRequestError):
        client.batch_create([req, req])


def test_batch_kiem_luat_truoc_khi_gui():
    client, mock = tao_client()
    with pytest.raises(ValueError, match="temperature"):
        client.batch_create([{"custom_id": "a", "params": {"messages": [{"role": "user", "content": "x"}],
                                                           "temperature": 0.2}}])
    assert mock.messages.batches._data == {}


def test_s5_continue_chi_gui_message_moi():
    client, mock = tao_client()
    t = S5.HoiThoaiThread(client, S5.SO_TAY, cache_control=S5.CACHE)
    for c in ("một", "hai", "ba"):
        t.gui(c)
    gui = mock.da_gui
    assert gui[0]["extra_body"]["thread"] == {"type": "create"} and "system" in gui[0]
    for req in gui[1:]:
        assert req["extra_body"]["thread"]["type"] == "continue"
        assert "system" not in req and "tools" not in req and len(req["messages"]) == 1
        assert req["extra_headers"]["anthropic-beta"] == "message-threads-2026-08-12"
    assert [d["cach"] for d in t.nhat_ky] == ["create", "continue", "continue"]
    doc = [d["usage"].cache_read_input_tokens for d in t.nhat_ky]
    assert doc[0] == 0 and doc[1] > 0 and doc[2] > doc[1]  # mỗi lượt đọc phần cũ từ cache
    assert len(t.messages) == 6  # bản sao của ứng dụng giữ cả hội thoại


def test_s5_het_han_thi_gui_lai_ca_hoi_thoai():
    client, mock = tao_client()
    t = S5.HoiThoaiThread(client, S5.SO_TAY)
    t.gui("một")
    t.gui("hai")
    mock.messages.het_han_threads()
    t.gui("ba")
    assert t.nhat_ky[-1]["cach"] == "gửi lại (404)"
    assert t.nhat_ky[-1]["so_message_gui"] == 5 == len(mock.da_gui[-1]["messages"])


def test_thread_loi_theo_docs():
    client, _ = tao_client()
    hoi = [{"role": "user", "content": "x"}]
    m = client.create(messages=hoi, thread={"type": "create"})
    tiep = {"type": "continue", "previous_message_id": m.id}
    client.create(messages=hoi, thread=tiep)
    with pytest.raises(anthropic.BadRequestError) as e:
        client.create(messages=hoi, thread=tiep)  # mỗi id chỉ tiếp tục một lần
    assert e.value.body["error"]["details"]["error_code"] == "thread_already_continued"
    m = client.create(messages=hoi, thread={"type": "create"})
    with pytest.raises(anthropic.BadRequestError) as e:
        client.create(messages=hoi, output_config={"effort": "low"},
                      thread={"type": "continue", "previous_message_id": m.id})
    assert e.value.body["error"]["details"]["error_code"] == "thread_fingerprint_mismatch"
    with pytest.raises(anthropic.BadRequestError):
        client.create(messages=hoi, system="khác", thread={"type": "continue", "previous_message_id": m.id})
    with pytest.raises(anthropic.NotFoundError):
        client.create(messages=hoi, thread={"type": "continue", "previous_message_id": "msg_khong_co"})
    with pytest.raises(anthropic.BadRequestError):  # token counting không dùng được với thread
        client._client.messages.count_tokens(model="claude-haiku-5-5", messages=hoi,
                                             extra_body={"thread": {"type": "create"}})


@pytest.mark.parametrize("params, loi", [
    ({"cache_control": {"type": "ephemeral"}, "system": [
        {"type": "text", "text": str(i), "cache_control": {"type": "ephemeral"}} for i in range(4)]}, "Tối đa 4"),
    ({"system": [{"type": "text", "text": "a", "cache_control": {"type": "ephemeral", "ttl": "10m"}}]}, "ttl"),
    ({"system": [{"type": "text", "text": "a", "cache_control": {"type": "ephemeral"}},
                 {"type": "text", "text": "b", "cache_control": {"type": "ephemeral", "ttl": "1h"}}]}, "1h"),
    ({"cache_control": {"type": "persistent"}}, "ephemeral"),
])
def test_rules_cache_control_sai(params, loi):
    with pytest.raises(ValueError, match=loi):
        check_request({"model": "claude-haiku-5-5", "max_tokens": 10, "messages": [{"role": "user", "content": "x"}],
                       **params})


# ---------- Bài 1 ----------

def _msg(model="claude-haiku-5-5", input_tokens=100, output=50, ghi=0, ghi_1h=0, doc=0, cache_creation=True):
    usage = {"input_tokens": input_tokens, "output_tokens": output, "cache_creation_input_tokens": ghi,
             "cache_read_input_tokens": doc}
    if cache_creation:
        usage["cache_creation"] = {"ephemeral_5m_input_tokens": ghi - ghi_1h, "ephemeral_1h_input_tokens": ghi_1h}
    return Message.model_validate({"id": "m", "type": "message", "role": "assistant", "model": model,
                                   "content": [{"type": "text", "text": "ok"}], "stop_reason": "end_turn",
                                   "stop_sequence": None, "usage": usage})


@pytest.mark.parametrize("model", ACTIVE)
@pytest.mark.parametrize("batch", [False, True])
def test_bai1_khop_estimate_cost_usd(model, batch):
    b1 = nap("bai1_chi_phi_cache")
    msg = _msg(model, ghi=3000, ghi_1h=1000, doc=5000)
    c = b1.chi_phi(msg, batch=batch)
    assert c["tong"] == pytest.approx(estimate_cost_usd(msg, batch=batch))
    assert c["tong"] == pytest.approx(sum(v for k, v in c.items() if k != "tong"))
    cache = MODELS[model]["cache_price_per_mtok"]
    he_so = 0.5 if batch else 1.0
    assert c["ghi_1h"] == pytest.approx(1000 * cache["write_1h"] / 1e6 * he_so)
    assert c["ghi_5m"] == pytest.approx(2000 * cache["write_5m"] / 1e6 * he_so)
    assert c["doc"] == pytest.approx(5000 * cache["read"] / 1e6 * he_so)


def test_bai1_truong_cache_none():
    b1 = nap("bai1_chi_phi_cache")
    msg = Message.model_validate({"id": "m", "type": "message", "role": "assistant", "model": "claude-haiku-5-5",
                                  "content": [], "stop_reason": "end_turn", "stop_sequence": None,
                                  "usage": {"input_tokens": 10, "output_tokens": 5}})
    c = b1.chi_phi(msg)
    assert c["ghi_5m"] == c["ghi_1h"] == c["doc"] == 0
    assert c["tong"] == pytest.approx(estimate_cost_usd(msg))
    assert b1.chi_phi(_msg(ghi=700, cache_creation=False))["ghi_5m"] == pytest.approx(
        700 * MODELS["claude-haiku-5-5"]["cache_price_per_mtok"]["write_5m"] / 1e6)


def test_bai1_model_chua_co_gia():
    b1 = nap("bai1_chi_phi_cache")
    with pytest.raises(ValueError):
        b1.chi_phi(_msg(model="claude-sonnet-4-5-20250929"))
    with pytest.raises(ValueError):
        b1.so_lan_doc_hoa_von("claude-khong-co")


def test_bai1_hoa_von_doc_gia_tu_config(monkeypatch):
    b1 = nap("bai1_chi_phi_cache")
    gia_gia = {"batch_price_multiplier": 0.5, "models": {"mo-hinh-gia": {
        "status": "active", "price_per_mtok": {"input": 1.0, "output": 5.0},
        "cache_price_per_mtok": {"write_5m": 3.0, "write_1h": 6.0, "read": 0.1}}}}
    monkeypatch.setattr(b1, "load_models", lambda: gia_gia)
    assert b1.so_lan_doc_hoa_von("mo-hinh-gia", "5m") == 3   # 3 + 0,1n < 1 + n  khi n >= 3
    assert b1.so_lan_doc_hoa_von("mo-hinh-gia", "1h") == 6   # 6 + 0,1n < 1 + n  khi n >= 6


@pytest.mark.parametrize("model", ACTIVE)
def test_bai1_hoa_von(model):
    b1 = nap("bai1_chi_phi_cache")
    assert b1.so_lan_doc_hoa_von(model, "5m") == 1
    assert b1.so_lan_doc_hoa_von(model, "1h") == 2
    with pytest.raises(ValueError):
        b1.so_lan_doc_hoa_von(model, "2h")


# ---------- Bài 2 ----------

def test_bai2_tran_chi_phi():
    b2 = nap("bai2_ngan_sach")
    client, mock = tao_client()
    params = {"messages": [{"role": "user", "content": "x"}], "max_tokens": 200}
    n = client.count_tokens(messages=params["messages"]).input_tokens
    gia = MODELS[client.settings.model]["price_per_mtok"]
    assert b2.tran_chi_phi(client, params) == pytest.approx((n * gia["input"] + 200 * gia["output"]) / 1e6)
    assert params["max_tokens"] == 200  # không sửa dict của người gọi
    assert mock.messages.calls == 0


def test_bai2_trong_ngan_sach_thi_goi():
    b2 = nap("bai2_ngan_sach")
    client, mock = tao_client()
    msg = b2.goi_trong_ngan_sach(client, {"messages": [{"role": "user", "content": "x"}]}, 1.0)
    assert msg.content and mock.messages.calls == 1 and mock.messages.count_calls == 1


def test_bai2_vuot_ngan_sach_thi_khong_goi():
    b2 = nap("bai2_ngan_sach")
    client, mock = tao_client()
    with pytest.raises(b2.VuotNganSach):
        b2.goi_trong_ngan_sach(client, {"messages": [{"role": "user", "content": "x"}]}, 1e-9)
    assert mock.messages.calls == 0 and mock.messages.count_calls == 1


def test_bai2_dung_model_trong_params():
    b2 = nap("bai2_ngan_sach")
    client, _ = tao_client()
    params = {"model": "claude-fable-5-2", "messages": [{"role": "user", "content": "x"}], "max_tokens": 100}
    assert b2.tran_chi_phi(client, params) > b2.tran_chi_phi(client, {**params, "model": "claude-haiku-5-5"})


# ---------- Bài 3 ----------

def test_bai3_tao_requests():
    b3 = nap("bai3_batch")
    reqs = b3.tao_requests({"mau-01": "Câu 1", "mau_02": "Câu 2"})
    assert reqs == [{"custom_id": "mau-01", "params": {"messages": [{"role": "user", "content": "Câu 1"}]}},
                    {"custom_id": "mau_02", "params": {"messages": [{"role": "user", "content": "Câu 2"}]}}]


@pytest.mark.parametrize("viec", [{}, {"mẫu 1": "x"}, {"a" * 65: "x"}, {"a/b": "x"}, {"ok\n": "x"}])
def test_bai3_tao_requests_sai(viec):
    with pytest.raises(ValueError):
        nap("bai3_batch").tao_requests(viec)


def _kq(custom_id, loai, model="claude-haiku-5-5"):
    result = {"type": loai}
    if loai == "succeeded":
        result["message"] = _msg(model).model_dump(mode="json")
    elif loai == "errored":
        result["error"] = {"type": "error", "error": {"type": "invalid_request_error", "message": "sai"}}
    return MessageBatchIndividualResponse.model_validate({"custom_id": custom_id, "result": result})


def test_bai3_gom_khong_phu_thuoc_thu_tu():
    b3 = nap("bai3_batch")
    ket_qua = [_kq("c", "expired"), _kq("a", "succeeded"), _kq("d", "errored"), _kq("b", "succeeded"),
               _kq("e", "canceled")]
    g = b3.gom(ket_qua)
    assert g["tra_loi"] == {"a": "ok", "b": "ok"}
    assert g["loi"] == {"c": "expired", "d": "errored", "e": "canceled"}
    assert g["usd"] == pytest.approx(2 * estimate_cost_usd(_msg(), batch=True))


def test_bai3_chay_that_qua_mock():
    b3 = nap("bai3_batch")
    client, _ = tao_client()
    batch = client.batch_create(b3.tao_requests({"x1": "Một", "x2": "Hai"}))
    while client.batch_retrieve(batch.id).processing_status != "ended":
        pass
    g = b3.gom(client.batch_results(batch.id))
    assert set(g["tra_loi"]) == {"x1", "x2"} and g["loi"] == {} and g["usd"] > 0


# ---------- Mock: các trường hợp review tìm ra ----------

def test_thread_loi_truoc_khi_model_chay_khong_doi_thread():
    client, mock = tao_client(errors=[])
    hoi = [{"role": "user", "content": "x"}]
    m = client.create(messages=hoi, thread={"type": "create"})
    mock.messages._errors.append(429)
    tiep = {"type": "continue", "previous_message_id": m.id}
    with pytest.raises(anthropic.RateLimitError):
        client.create(messages=hoi, thread=tiep)
    assert client.create(messages=hoi, thread=tiep).id != m.id  # thử lại cùng request: được


def test_thread_breakpoint_da_luu_van_doc_duoc_cache():
    client, _ = tao_client()
    dau = [{"role": "user", "content": [{"type": "text", "text": S2.SO_TAY, "cache_control": {"type": "ephemeral"}}]}]
    m = client.create(messages=dau, thread={"type": "create"})
    assert m.usage.cache_creation_input_tokens > 0
    m2 = client.create(messages=[{"role": "user", "content": "tiếp"}],
                       thread={"type": "continue", "previous_message_id": m.id})
    assert m2.usage.cache_read_input_tokens == m.usage.cache_creation_input_tokens


def test_thread_continue_thieu_id_la_400():
    client, _ = tao_client()
    with pytest.raises(anthropic.BadRequestError):
        client.create(messages=[{"role": "user", "content": "x"}], thread={"type": "continue"})


def test_thread_giu_beta_header_cua_nguoi_goi():
    client, mock = tao_client()
    client.create(messages=[{"role": "user", "content": "x"}], thread={"type": "create"},
                  extra_headers={"anthropic-beta": "beta-khac-2026-01-01"})
    assert mock.da_gui[-1]["extra_headers"]["anthropic-beta"] == "beta-khac-2026-01-01,message-threads-2026-08-12"


def test_cache_tron_ttl_doc_5m_ma_1h_truot_thi_khong_doc():
    client, _ = tao_client()
    hoi = [{"role": "user", "content": "x"}]
    client.create(system=[{"type": "text", "text": S2.SO_TAY, "cache_control": {"type": "ephemeral"}}], messages=hoi)
    system = [{"type": "text", "text": S2.SO_TAY, "cache_control": {"type": "ephemeral", "ttl": "1h"}},
              {"type": "text", "text": "thêm " * 200, "cache_control": {"type": "ephemeral", "ttl": "1h"}}]
    msg = client.create(system=system, messages=hoi)
    assert msg.usage.cache_read_input_tokens == 0 and msg.usage.cache_creation.ephemeral_1h_input_tokens > 0


def test_rules_ttl_cap_cao_khac_block_cuoi():
    with pytest.raises(ValueError, match="ttl khác"):
        check_request({"model": "claude-haiku-5-5", "max_tokens": 10, "cache_control": {"type": "ephemeral"},
                       "messages": [{"role": "user", "content": [
                           {"type": "text", "text": "x", "cache_control": {"type": "ephemeral", "ttl": "1h"}}]}]})


def test_batch_errored_giu_loai_loi_that():
    client, mock = tao_client()
    batch = client.batch_create(S4.tao_requests(["a"]))
    mock.messages._errors.append(529)
    client.batch_retrieve(batch.id)
    client.batch_retrieve(batch.id)
    (r,) = client.batch_results(batch.id)
    assert r.result.type == "errored" and r.result.error.error.type == "overloaded_error"


def test_client_mock_tra_ve_mock():
    client, mock = tao_client()
    assert client.mock is mock
