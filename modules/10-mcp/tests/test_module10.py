"""Chấm module 10 (không gọi Claude thật, không cần mạng, không cần API key).

    CLAUDE_MOCK=1 uv run pytest modules/10-mcp -q                    # chấm lời giải
    CHAM=exercises CLAUDE_MOCK=1 uv run pytest modules/10-mcp -q     # chấm bài của bạn

Server được nối trong process (Client(server)) cho nhanh; script 01–03 thì chạy thật qua stdio.
"""
import asyncio
import importlib.util
import json
import sys
from pathlib import Path

import pytest
from claude_vi import check_request
from claude_vi.cham import nap as _nap
from mcp import Client
from mcp.types import CallToolResult, ImageContent, TextContent, Tool, ToolAnnotations

MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE / "python"))

import cau_noi as CN  # noqa: E402
import may_chu_ptn as MC  # noqa: E402


def _nap_py(ten):
    spec = importlib.util.spec_from_file_location(f"module10_{ten}", MODULE / "python" / f"{ten}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


S1, S2, S3 = (_nap_py(t) for t in ("01_kham_pha_may_chu", "02_goi_tool", "03_claude_dung_mcp"))


def nap(ten):
    return _nap(MODULE, ten)


def voi(server, coro_fn):
    async def _():
        async with Client(server) as c:
            return await coro_fn(c)
    return asyncio.run(_())


@pytest.fixture(autouse=True)
def _moi_truong(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_MOCK", "1")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(MC, "NHAT_KY", tmp_path / "nhat_ky.txt")


# ---------- Server mẫu và script ----------

@pytest.mark.parametrize("script, phai_co", [
    (S1, ["2026-07-28", "tra_lich", "ptn://so-tay", "hoi_lich"]),
    (S2, ["Error executing tool xem_mau", "noi_dung rỗng", "Unknown tool"]),
    (S3, ["không được duyệt", "(host cho chạy không cần hỏi)"]),
], ids=["01", "02", "03"])
def test_script_chay_qua_stdio(script, phai_co, capsys, monkeypatch, tmp_path):
    # Server là process con: chỉ đổi được file nhật ký của nó qua env truyền vào StdioServerParameters
    goc = CN.tham_so_stdio
    monkeypatch.setattr(CN, "tham_so_stdio", lambda env=None: goc({"MODULE10_NHAT_KY": str(tmp_path / "nk.txt")}))
    for mod in (S1, S2, S3):
        monkeypatch.setattr(mod, "tham_so_stdio", CN.tham_so_stdio)
    asyncio.run(script.main())
    out = capsys.readouterr().out
    assert all(x in out for x in phai_co)
    if script is S3:
        assert (tmp_path / "nk.txt").read_text("utf-8").strip()  # lần được duyệt đã ghi vào file của test


def test_may_chu_khai_bao_du_ba_primitive():
    async def xem(c):
        return await c.list_tools(), await c.list_resources(), await c.list_prompts()
    tools, res, prompts = voi(MC.server, xem)
    by = {t.name: t for t in tools.tools}
    assert set(by) == {"tra_lich", "xem_mau", "ghi_nhat_ky"}
    assert by["tra_lich"].input_schema["properties"]["ma_thiet_bi"]["enum"] == list(MC.LICH)
    assert by["tra_lich"].output_schema and by["tra_lich"].annotations.read_only_hint is True
    assert by["ghi_nhat_ky"].annotations.read_only_hint is False
    assert [str(r.uri) for r in res.resources] == ["ptn://so-tay"]
    assert [p.name for p in prompts.prompts] == ["hoi_lich"]


def test_tool_tra_ve_structured_va_text():
    kq = voi(MC.server, lambda c: c.call_tool("tra_lich", {"ma_thiet_bi": "QS-3"}))
    assert kq.is_error is False and kq.structured_content == {"ma_thiet_bi": "QS-3", "lich": MC.LICH["QS-3"]}
    assert json.loads(kq.content[0].text) == kq.structured_content  # text cũng mang cùng dữ liệu


@pytest.mark.parametrize("ten, args, chu", [
    ("tra_lich", {"ma_thiet_bi": "XX-1"}, "validation"),
    ("ghi_nhat_ky", {"noi_dung": " "}, "noi_dung rỗng"),   # ToolError: lời nhắn tới được client
    ("khong_co", {}, "Unknown tool"),
    ("xem_mau", {"ma_mau": "M-99"}, "Error executing tool xem_mau"),   # crash: chỉ còn lời nhắn chung
])
def test_loi_tool_la_is_error_co_loi_nhan(ten, args, chu):
    kq = voi(MC.server, lambda c: c.call_tool(ten, args))
    assert kq.is_error is True and chu in kq.content[0].text


def test_crash_giau_loi_nhan_goc():
    kq = voi(MC.server, lambda c: c.call_tool("xem_mau", {"ma_mau": "M-99"}))
    assert kq.content[0].text == "Error executing tool xem_mau" and "M-99" not in kq.content[0].text


def test_cau_noi_sang_tool_result_anh_va_block_la():
    from mcp.types import EmbeddedResource, TextResourceContents
    kq = CallToolResult(is_error=False, content=[
        TextContent(type="text", text="a"), ImageContent(type="image", data="aGk=", mime_type="image/png"),
        EmbeddedResource(type="resource", resource=TextResourceContents(uri="ptn://x", text="t"))])
    r = CN.sang_tool_result("t1", kq)
    assert r["content"][0] == {"type": "text", "text": "a"}
    assert r["content"][1] == {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "aGk="}}
    assert "resource" in r["content"][2]["text"]
    assert CN.sang_tool_result("t2", CallToolResult(content=[], is_error=True)) == {
        "type": "tool_result", "tool_use_id": "t2", "content": [{"type": "text", "text": "(không có nội dung)"}],
        "is_error": True}


def test_ghi_nhat_ky_ghi_file():
    kq = voi(MC.server, lambda c: c.call_tool("ghi_nhat_ky", {"noi_dung": "Đã hiệu chuẩn HV-200"}))
    assert kq.is_error is False and MC.NHAT_KY.read_text("utf-8") == "Đã hiệu chuẩn HV-200\n"


def test_cau_noi_sang_tool_claude_hop_le_voi_messages_api():
    tools = CN.sang_tool_claude(voi(MC.server, lambda c: c.list_tools()).tools)
    check_request({"model": "claude-haiku-5-5", "max_tokens": 10, "tools": tools,
                   "messages": [{"role": "user", "content": "x"}]})
    assert {t["name"] for t in tools} == {"tra_lich", "xem_mau", "ghi_nhat_ky"}


def test_s3_host_duyet_va_goi_mcp():
    async def chay(duyet):
        async with Client(MC.server) as mcp:
            return await S3.hoi(CN.tao_claude(), mcp, "Tra lịch HV-200 rồi ghi nhật ký.", lambda n, a: duyet)
    tu_choi = asyncio.run(chay(False))
    assert tu_choi["nhat_ky"] == [("tra_lich", "chạy"), ("ghi_nhat_ky", "không được duyệt"), ("xem_mau", "lỗi")]
    assert not MC.NHAT_KY.exists()
    duoc = asyncio.run(chay(True))
    assert duoc["nhat_ky"] == [("tra_lich", "chạy"), ("ghi_nhat_ky", "chạy"), ("xem_mau", "lỗi")]
    assert MC.NHAT_KY.exists() and duoc["usd"] > 0 and duoc["so_luot"] == 4
    assert duoc["stop_reason"] == "end_turn" and duoc["het_luot"] is False


def test_s3_bao_het_luot(monkeypatch):
    monkeypatch.setattr(S3, "TOI_DA_LUOT", 1)

    async def chay():
        async with Client(MC.server) as mcp:
            return await S3.hoi(CN.tao_claude(), mcp, "Tra lịch HV-200.", lambda n, a: True)
    kq = asyncio.run(chay())
    assert kq["het_luot"] is True and kq["stop_reason"] == "tool_use"


def test_annotation_khong_lam_host_bo_duyet():
    assert CN.can_duyet("ghi_nhat_ky") is True and CN.can_duyet("tra_lich") is False
    assert CN.can_duyet("khong_co_trong_danh_sach") is True


# ---------- Bài 1 ----------

def _b1():
    return nap("bai1_may_chu").tao_may_chu()


@pytest.mark.parametrize("vao, ra", [({"gia_tri": 100, "don_vi": "C"}, {"gia_tri": 212.0, "don_vi": "F"}),
                                     ({"gia_tri": 212, "don_vi": "F"}, {"gia_tri": 100.0, "don_vi": "C"}),
                                     ({"gia_tri": 36.6, "don_vi": "C"}, {"gia_tri": 97.9, "don_vi": "F"}),
                                     ({"gia_tri": -400, "don_vi": "F"}, {"gia_tri": -240.0, "don_vi": "C"}),
                                     ({"gia_tri": -273.15, "don_vi": "C"}, {"gia_tri": -459.7, "don_vi": "F"})])
def test_bai1_doi_nhiet(vao, ra):
    kq = voi(_b1(), lambda c: c.call_tool("doi_nhiet_do", vao))
    assert kq.is_error is False and kq.structured_content == ra


def test_bai1_schema_va_annotation():
    t = voi(_b1(), lambda c: c.list_tools()).tools
    assert [x.name for x in t] == ["doi_nhiet_do"] and t[0].description
    p = t[0].input_schema["properties"]
    assert p["don_vi"]["enum"] == ["C", "F"] and p["gia_tri"]["type"] == "number"
    assert set(t[0].input_schema["required"]) == {"gia_tri", "don_vi"}
    assert set(t[0].output_schema["properties"]) == {"gia_tri", "don_vi"}
    assert t[0].annotations.read_only_hint is True and t[0].annotations.idempotent_hint is True


@pytest.mark.parametrize("vao", [{"gia_tri": -300, "don_vi": "C"}, {"gia_tri": -500, "don_vi": "F"}])
def test_bai1_duoi_khong_tuyet_doi(vao):
    kq = voi(_b1(), lambda c: c.call_tool("doi_nhiet_do", vao))
    assert kq.is_error is True and "độ không tuyệt đối" in kq.content[0].text


def test_bai1_don_vi_sai_bi_schema_chan():
    kq = voi(_b1(), lambda c: c.call_tool("doi_nhiet_do", {"gia_tri": 1, "don_vi": "K"}))
    assert kq.is_error is True


def test_bai1_resource():
    async def doc(c):
        return await c.list_resources(), await c.read_resource("dv://don-vi")
    ds, nd = voi(_b1(), doc)
    assert [str(r.uri) for r in ds.resources] == ["dv://don-vi"] and ds.resources[0].mime_type == "text/plain"
    assert nd.contents[0].text == "C, F"


# ---------- Bài 2 ----------

def _tool(ten, mo_ta="m", annotations=None):
    return Tool(name=ten, description=mo_ta, input_schema={"type": "object", "properties": {}},
                annotations=annotations)


def test_bai2_dat_tien_to_va_bang_tra():
    ds, bang = nap("bai2_cau_noi").sang_tool_claude([_tool("tra_lich"), _tool("lich.tra/v2", None)], "ptn")
    assert [t["name"] for t in ds] == ["ptn__tra_lich", "ptn__lich_tra_v2"]
    assert bang == {"ptn__tra_lich": "tra_lich", "ptn__lich_tra_v2": "lich.tra/v2"}
    assert ds[1]["description"] == "" and ds[0]["input_schema"] == {"type": "object", "properties": {}}
    check_request({"model": "claude-haiku-5-5", "max_tokens": 10, "tools": ds,
                   "messages": [{"role": "user", "content": "x"}]})


def test_bai2_cat_128_ky_tu():
    ds, _ = nap("bai2_cau_noi").sang_tool_claude([_tool("x" * 200)], "srv")
    assert len(ds[0]["name"]) == 128 and ds[0]["name"].startswith("srv__")


def test_bai2_sua_ca_tien_to():
    ds, bang = nap("bai2_cau_noi").sang_tool_claude([_tool("a")], "my.srv")
    assert ds[0]["name"] == "my_srv__a" and bang == {"my_srv__a": "a"}


@pytest.mark.parametrize("tools, tien_to", [([_tool("a.b"), _tool("a/b")], "p"), ([_tool("a")], ""),
                                            ([_tool("x" * 200 + "1"), _tool("x" * 200 + "2")], "p")])
def test_bai2_loi(tools, tien_to):
    with pytest.raises(ValueError):
        nap("bai2_cau_noi").sang_tool_claude(tools, tien_to)


# ---------- Bài 3 ----------

@pytest.mark.parametrize("ann, trong_ds, can", [
    (None, False, True),
    (ToolAnnotations(read_only_hint=True), False, True),        # server tự nhận "chỉ đọc": vẫn phải hỏi
    (None, True, False),
    (ToolAnnotations(read_only_hint=True), True, False),
    (ToolAnnotations(destructive_hint=True), True, True),       # annotation chỉ làm host thận trọng hơn
    (ToolAnnotations(destructive_hint=False), True, False),
])
def test_bai3_can_duyet(ann, trong_ds, can):
    t = _tool("xoa_mau", annotations=ann)
    assert nap("bai3_duyet").can_duyet(t, {"xoa_mau"} if trong_ds else {"khac"}) is can


def _kq(content, structured=None, loi=False):
    return CallToolResult(content=content, structured_content=structured, is_error=loi)


@pytest.mark.parametrize("kq, mong", [
    (_kq([TextContent(type="text", text="a"), TextContent(type="text", text="b")]), ["a", "b"]),
    (_kq([], {"x": "độ"}), ['{"x": "độ"}']),
    (_kq([TextContent(type="text", text="t")], {"x": 1}), ["t"]),
    (_kq([]), ["(không có nội dung)"]),
    (_kq([], {}), ["{}"]),
    (_kq([TextContent(type="text", text="a"), ImageContent(type="image", data="aGk=", mime_type="image/png")]), ["a"]),
    (_kq([ImageContent(type="image", data="aGk=", mime_type="image/png")], {"x": 1}), ['{"x": 1}']),
])
def test_bai3_sang_tool_result(kq, mong):
    r = nap("bai3_duyet").sang_tool_result("toolu_1", kq)
    assert r["type"] == "tool_result" and r["tool_use_id"] == "toolu_1" and r["is_error"] is False
    assert r["content"] == [{"type": "text", "text": m} for m in mong]


def test_bai3_giu_is_error():
    r = nap("bai3_duyet").sang_tool_result("t", _kq([TextContent(type="text", text="hỏng")], loi=True))
    assert r["is_error"] is True
