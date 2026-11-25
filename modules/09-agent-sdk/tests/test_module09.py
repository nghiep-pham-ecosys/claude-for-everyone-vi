"""Chấm module 09 (mock mode, không gọi mạng, không cần claude-agent-sdk).

    CLAUDE_MOCK=1 uv run pytest modules/09-agent-sdk -q                    # chấm lời giải
    CHAM=exercises CLAUDE_MOCK=1 uv run pytest modules/09-agent-sdk -q     # chấm bài của bạn
"""
import asyncio
import importlib.util
import sys
from pathlib import Path

import pytest
from claude_vi import agent_sdk_mock as sdk
from claude_vi.agent_sdk import nap_sdk
from claude_vi.cham import nap as _nap

MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE / "python"))


def _nap_py(ten):
    spec = importlib.util.spec_from_file_location(f"module09_{ten}", MODULE / "python" / f"{ten}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


import cong_cu as CC  # noqa: E402  cùng module object mà các script import

S1, S2, S3 = (_nap_py(t) for t in ("01_query_dau_tien", "02_quyen_va_hook", "03_gioi_han_va_phien"))
TRA, GHI = "mcp__ptn__tra_lich", "mcp__ptn__ghi_nhat_ky"


def nap(ten):
    return _nap(MODULE, ten)


def chay(prompt, options):
    async def _():
        return [m async for m in sdk.query(prompt=prompt, options=options)]
    return asyncio.run(_())


def chay_bat_loi(prompt, options):
    out = []

    async def _():
        async for m in sdk.query(prompt=prompt, options=options):
            out.append(m)
    with pytest.raises(sdk.ResultError) as e:
        asyncio.run(_())
    return out, e.value


@pytest.fixture(autouse=True)
def _phien_sach(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_MOCK", "1")
    monkeypatch.setattr(CC, "NHAT_KY", tmp_path / "nhat_ky.txt")
    monkeypatch.setattr(S2, "NHAT_KY", tmp_path / "nhat_ky.txt")
    sdk._xoa_phien()


def _options(**them):
    return CC.options_co_ban(sdk, **{"mcp_servers": {"ptn": CC.tao_server(sdk)}, **them})


# ---------- Script ----------

@pytest.mark.parametrize("script", [S1, S2, S3], ids=["01", "02", "03"])
def test_script_chay_mock_khong_can_key(script, monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    asyncio.run(script.main())
    assert capsys.readouterr().out.strip()


def test_nap_sdk_mock_khong_can_goi_that():
    assert nap_sdk() is sdk


def test_nap_sdk_that_bao_loi_ro_khi_chua_cai(monkeypatch):
    from claude_vi import Settings
    from claude_vi.agent_sdk import MissingSdkError
    monkeypatch.setitem(sys.modules, "claude_agent_sdk", None)  # giả lập chưa cài
    with pytest.raises(MissingSdkError, match="CLAUDE_MOCK=1"):
        nap_sdk(Settings(model="claude-haiku-5-5", max_tokens=512, mock=False, record=False))


def test_luong_message_dung_thu_tu():
    msgs = chay("Lịch HV-200?", _options(allowed_tools=[TRA], disallowed_tools=[GHI]))
    assert isinstance(msgs[0], sdk.SystemMessage) and msgs[0].subtype == "init"
    assert msgs[0].data["tools"] == [TRA]                      # disallowed_tools tên trần: bỏ hẳn tool
    assert isinstance(msgs[-1], sdk.ResultMessage) and msgs[-1].subtype == "success"
    goi = [b for m in msgs if isinstance(m, sdk.AssistantMessage) for b in m.content if isinstance(b, sdk.ToolUseBlock)]
    assert [b.name for b in goi] == [TRA] and goi[0].input == {"ma_thiet_bi": "HV-200"}
    assert msgs[-1].num_turns == 2                             # một lượt gọi tool + một lượt trả lời
    assert msgs[-1].session_id == msgs[0].data["session_id"]
    assert all(len(m.content) == 1 for m in msgs if isinstance(m, sdk.AssistantMessage))


def test_khong_ai_duyet_thi_tu_choi():
    msgs = chay("Tra lịch rồi ghi.", _options(allowed_tools=[TRA]))
    assert [d["tool_name"] for d in msgs[-1].permission_denials] == [GHI]
    assert not CC.NHAT_KY.exists()


def test_can_use_tool_chi_duoc_hoi_khi_chua_ai_duyet():
    hoi = []
    msgs = chay("Tra lịch rồi ghi.", _options(allowed_tools=[TRA], can_use_tool=S2.tao_can_use_tool(sdk, hoi)))
    assert hoi == [GHI] and msgs[-1].permission_denials == []
    assert CC.NHAT_KY.read_text("utf-8").startswith("[agent] ")   # updated_input có hiệu lực


def test_hook_chan_ca_tool_da_duoc_allowed():
    hooks = {"PreToolUse": [sdk.HookMatcher(matcher="^mcp__ptn__", hooks=[S2.hook_chan_tu_cam])]}
    msgs = chay("Hãy xoá lịch QS-3.", _options(allowed_tools=["mcp__ptn__*"], hooks=hooks))
    assert [d["tool_name"] for d in msgs[-1].permission_denials] == [GHI]


def test_disallowed_thang_ca_bypass():
    msgs = chay("Ghi nhật ký.", _options(permission_mode="bypassPermissions", disallowed_tools=[GHI]))
    assert GHI not in msgs[0].data["tools"]


def test_max_turns_va_ngan_sach():
    msgs, loi = chay_bat_loi("x", _options(allowed_tools=["mcp__ptn__*"], max_turns=1))
    assert msgs[-1].subtype == "error_max_turns" and loi.subtype == "error_max_turns" and msgs[-1].num_turns == 1
    assert loi.data["stop_reason"] == "tool_use" and msgs[-1].errors and "turns" in msgs[-1].errors[0]
    msgs, loi = chay_bat_loi("x", _options(allowed_tools=["mcp__ptn__*"], max_budget_usd=1e-9))
    assert msgs[-1].subtype == "error_max_budget_usd" and msgs[-1].is_error


def test_resume_gom_chi_phi_cu_fork_ra_id_moi():
    dau = chay("Lịch HV-200?", _options(allowed_tools=[TRA]))[-1]
    sau = chay("Tóm tắt.", CC.options_co_ban(sdk, resume=dau.session_id))[-1]
    assert sau.session_id == dau.session_id and sau.total_cost_usd > dau.total_cost_usd
    re_nhanh = chay("Tóm tắt.", CC.options_co_ban(sdk, resume=dau.session_id, fork_session=True))[-1]
    assert re_nhanh.session_id != dau.session_id and re_nhanh.total_cost_usd > dau.total_cost_usd


async def _sai_ma(tool_name, input_data, context):
    return sdk.PermissionResultAllow(updated_input={"ma_thiet_bi": "XX-1"})


def test_input_sai_schema_bi_chan_truoc_handler():
    # SDK kiểm input theo schema trước khi gọi handler: ngoài enum thì handler không chạy
    msgs = chay("Lịch?", _options(can_use_tool=_sai_ma, disallowed_tools=[GHI]))
    ket = [b for m in msgs if isinstance(m, sdk.UserMessage) for b in m.content]
    assert ket[0].is_error is True and ket[0].content[0]["text"].startswith("Input validation error")
    assert msgs[-1].permission_denials == []   # được duyệt, chỉ là input sai


def test_handler_loi_va_exception_thanh_ket_qua_loi():
    @sdk.tool("hong", "Tool luôn ném lỗi", {"x": str})
    async def hong(args):
        raise RuntimeError("hỏng")
    o = CC.options_co_ban(sdk, mcp_servers={"t": sdk.create_sdk_mcp_server("t", tools=[hong])},
                          allowed_tools=["mcp__t__hong"])
    ket = [b for m in chay("x", o) if isinstance(m, sdk.UserMessage) for b in m.content]
    assert ket[0].is_error is True and "hỏng" in ket[0].content[0]["text"]


@pytest.mark.parametrize("allowed, duoc", [(["mcp__*"], False), (["*"], False), (["mcp__ptn__*"], True),
                                          (["mcp__ptn__tra_*"], True), ([TRA], True)])
def test_luat_allow_glob(allowed, duoc):
    msgs = chay("Lịch HV-200?", _options(allowed_tools=allowed, disallowed_tools=[GHI]))
    assert (msgs[-1].permission_denials == []) is duoc


@pytest.mark.parametrize("deny", [["*"], ["mcp__*"], ["mcp__ptn__*"]])
def test_luat_deny_glob_bo_moi_tool(deny):
    assert chay("x", _options(permission_mode="bypassPermissions", disallowed_tools=deny))[0].data["tools"] == []


def test_matcher_ten_chinh_xac_khong_khop_chuoi_con():
    goi = []

    async def ghi_lai(input_data, tool_use_id, context):
        goi.append(input_data["tool_name"])
        return {}
    for matcher, mong in [("ghi_nhat_ky", []), (GHI, [GHI]), (f"{TRA}|{GHI}", [TRA, GHI]), ("^mcp__ptn__", [TRA, GHI])]:
        goi.clear()
        chay("x", _options(allowed_tools=["mcp__ptn__*"],
                           hooks={"PreToolUse": [sdk.HookMatcher(matcher=matcher, hooks=[ghi_lai])]}))
        assert goi == mong, matcher


def test_hook_loi_mo_cua_tru_khi_block():
    async def hong(input_data, tool_use_id, context):
        raise RuntimeError("hook hỏng")
    msgs = chay("x", _options(allowed_tools=["mcp__ptn__*"], hooks={"PreToolUse": [sdk.HookMatcher(hooks=[hong])]}))
    assert msgs[-1].permission_denials == []                       # mặc định: lời gọi đi tiếp
    msgs = chay("x", _options(allowed_tools=["mcp__ptn__*"],
                              hooks={"PreToolUse": [sdk.HookMatcher(hooks=[hong], on_failure="block")]}))
    assert len(msgs[-1].permission_denials) == 2


def test_resume_id_la_thi_loi():
    msgs, loi = chay_bat_loi("x", CC.options_co_ban(sdk, resume="00000000-0000-4000-8000-999999999999"))
    assert msgs[-1].subtype == "error_during_execution" and loi.exit_code == 1


# ---------- Bài 1 ----------

def test_bai1_tom_tat_lan_chay_thanh_cong():
    b1 = nap("bai1_doc_ket_qua")
    msgs = chay("Tra lịch HV-200 rồi ghi.", _options(allowed_tools=[TRA]))
    t = b1.tom_tat(sdk, msgs)
    assert t == {"session_id": msgs[-1].session_id, "tools_da_goi": [TRA, GHI], "tool_loi": 1,
                 "so_luot": 3, "usd": msgs[-1].total_cost_usd, "tra_loi": msgs[-1].result, "thanh_cong": True}


def test_bai1_lan_chay_loi():
    b1 = nap("bai1_doc_ket_qua")
    msgs, _ = chay_bat_loi("x", _options(allowed_tools=["mcp__ptn__*"], max_turns=1))
    t = b1.tom_tat(sdk, msgs)
    assert t["thanh_cong"] is False and t["tra_loi"] is None and t["so_luot"] == 1


def test_bai1_usd_none_va_success_co_is_error():
    b1 = nap("bai1_doc_ket_qua")
    r = sdk.ResultMessage(subtype="success", duration_ms=0, duration_api_ms=0, is_error=True, num_turns=1,
                          session_id="s", total_cost_usd=None, result="x")
    t = b1.tom_tat(sdk, [r])
    assert t["usd"] is None and t["thanh_cong"] is False and t["tools_da_goi"] == [] and t["tool_loi"] == 0
    assert t["tra_loi"] == "x"
    r2 = sdk.ResultMessage(subtype="error_max_turns", duration_ms=0, duration_api_ms=0, is_error=False, num_turns=2,
                           session_id="s")
    assert b1.tom_tat(sdk, [r2])["thanh_cong"] is False


def test_bai1_tool_loi_khong_phai_tu_choi():
    b1 = nap("bai1_doc_ket_qua")
    msgs = chay("Lịch?", _options(can_use_tool=_sai_ma, disallowed_tools=[GHI]))
    assert msgs[-1].permission_denials == [] and b1.tom_tat(sdk, msgs)["tool_loi"] == 1


def test_bai1_thieu_result():
    with pytest.raises(ValueError):
        nap("bai1_doc_ket_qua").tom_tat(sdk, [sdk.SystemMessage("init", {"session_id": "s"})])


# ---------- Bài 2 ----------

def _goi(cb, ten, vao):
    return asyncio.run(cb(ten, vao, sdk.ToolPermissionContext(tool_use_id="t1")))


def test_bai2_tra_luon_duoc():
    cb = nap("bai2_quyen").tao_can_use_tool(sdk, cho_phep_ghi=False)
    kq = _goi(cb, "mcp__ptn__tra_lich", {"ma_thiet_bi": "HV-200"})
    assert isinstance(kq, sdk.PermissionResultAllow) and kq.updated_input is None


@pytest.mark.parametrize("cho_phep, noi_dung, duoc", [
    (True, "ngắn", True), (True, "x" * 200, True), (True, "x" * 201, False), (False, "ngắn", False)])
def test_bai2_ghi_nhat_ky(cho_phep, noi_dung, duoc):
    cb = nap("bai2_quyen").tao_can_use_tool(sdk, cho_phep_ghi=cho_phep)
    vao = {"noi_dung": noi_dung}
    kq = _goi(cb, GHI, vao)
    assert vao == {"noi_dung": noi_dung}  # không sửa input gốc
    if duoc:
        assert isinstance(kq, sdk.PermissionResultAllow) and kq.updated_input == {"noi_dung": f"[agent] {noi_dung}"}
    else:
        assert isinstance(kq, sdk.PermissionResultDeny) and kq.message


@pytest.mark.parametrize("ten", ["mcp__khac__tra_lich", "Bash", "mcp__ptn__xoa_lich"])
def test_bai2_tool_la_bi_tu_choi(ten):
    kq = _goi(nap("bai2_quyen").tao_can_use_tool(sdk, cho_phep_ghi=True), ten, {})
    assert isinstance(kq, sdk.PermissionResultDeny) and kq.message


@pytest.mark.parametrize("vao, chan", [
    ({"noi_dung": "XOÁ dòng 3"}, True), ({"noi_dung": "hủy lịch"}, True), ({"a": {"b": ["xóa"]}}, True),
    ({"noi_dung": "Thêm dòng mới"}, False), ({}, False)])
def test_bai2_hook(vao, chan):
    out = asyncio.run(nap("bai2_quyen").hook_chi_them({"hook_event_name": "PreToolUse", "tool_name": GHI,
                                                        "tool_input": vao}, "t1", None))
    if chan:
        h = out["hookSpecificOutput"]
        assert h["hookEventName"] == "PreToolUse" and h["permissionDecision"] == "deny" and h["permissionDecisionReason"]
    else:
        assert out == {}


def test_bai2_chay_cung_agent():
    b2 = nap("bai2_quyen")
    hooks = {"PreToolUse": [sdk.HookMatcher(matcher="^mcp__ptn__", hooks=[b2.hook_chi_them])]}
    msgs = chay("Ghi nhật ký: hủy ca đêm.", _options(can_use_tool=b2.tao_can_use_tool(sdk, True), hooks=hooks))
    assert [d["tool_name"] for d in msgs[-1].permission_denials] == [GHI]


# ---------- Bài 3 ----------

@pytest.mark.parametrize("vao, ra", [({"gia_tri": 100, "don_vi": "C"}, "212.0 F"),
                                     ({"gia_tri": 212, "don_vi": "F"}, "100.0 C"),
                                     ({"gia_tri": -40, "don_vi": "C"}, "-40.0 F")])
def test_bai3_doi_nhiet(vao, ra):
    t = nap("bai3_tuy_chon").tao_tool_doi_nhiet(sdk)
    assert t.name == "doi_nhiet_do" and t.description
    schema = t.input_schema
    assert schema["properties"]["don_vi"]["enum"] == ["C", "F"] and set(schema["required"]) == {"gia_tri", "don_vi"}
    assert schema["properties"]["gia_tri"]["type"] == "number" and schema["properties"]["don_vi"]["type"] == "string"
    out = asyncio.run(t.handler(vao))
    assert out["content"] == [{"type": "text", "text": ra}] and not out.get("is_error")


def test_bai3_don_vi_sai():
    out = asyncio.run(nap("bai3_tuy_chon").tao_tool_doi_nhiet(sdk).handler({"gia_tri": 1, "don_vi": "K"}))
    assert out["is_error"] is True and "C" in out["content"][0]["text"] and "F" in out["content"][0]["text"]


@pytest.mark.parametrize("chi_doc", [True, False])
def test_bai3_options(chi_doc):
    b3 = nap("bai3_tuy_chon")
    server = CC.tao_server(sdk)
    o = b3.tao_options(sdk, server, chi_doc=chi_doc, ngan_sach_usd=0.02)
    assert isinstance(o, sdk.ClaudeAgentOptions)
    assert o.mcp_servers == {"ptn": server} and o.tools == [] and o.setting_sources == []
    assert o.max_turns == 5 and o.max_budget_usd == 0.02 and o.permission_mode == "dontAsk"
    if chi_doc:
        assert o.allowed_tools == [TRA] and o.disallowed_tools == [GHI]
    else:
        assert o.allowed_tools == ["mcp__ptn__*"] and o.disallowed_tools == []
    msgs = chay("Tra lịch QS-3 rồi ghi.", o)
    assert msgs[-1].subtype == "success"
    assert (GHI in msgs[0].data["tools"]) is (not chi_doc)


@pytest.mark.parametrize("ngan_sach", [0, -1])
def test_bai3_ngan_sach_sai(ngan_sach):
    with pytest.raises(ValueError):
        nap("bai3_tuy_chon").tao_options(sdk, CC.tao_server(sdk), True, ngan_sach)
