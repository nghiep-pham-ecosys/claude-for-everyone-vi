import json

import anthropic
import pytest

from claude_vi import ClaudeVi, ModelRuleError, Settings, check_request, estimate_cost_usd, text_of
from claude_vi.mock import MockAnthropic, request_key


@pytest.fixture
def mock_client(tmp_path):
    s = Settings(model="claude-haiku-5-5", max_tokens=512, mock=True, record=False)
    return ClaudeVi(settings=s, client=MockAnthropic(record_dir=tmp_path)), tmp_path


def test_default_mock_skips_thinking_block(mock_client):
    c, _ = mock_client
    msg = c.ask("Xin chào")
    assert msg.content[0].type == "thinking"          # giống model 5.x thật
    assert text_of(msg).startswith("[MOCK]")


def test_fixture_is_validated_by_sdk_types(mock_client):
    c, d = mock_client
    params = {"model": "claude-haiku-5-5", "messages": [{"role": "user", "content": "1+1?"}]}
    (d / f"{request_key(params)}.json").write_text(json.dumps({
        "id": "msg_x", "type": "message", "role": "assistant", "model": "claude-haiku-5-5",
        "content": [{"type": "text", "text": "2"}], "stop_reason": "end_turn",
        "stop_sequence": None, "usage": {"input_tokens": 5, "output_tokens": 1},
    }))
    assert text_of(c.create(**params)) == "2"


def test_broken_fixture_fails_loudly(mock_client):
    c, d = mock_client
    params = {"model": "claude-haiku-5-5", "messages": [{"role": "user", "content": "x"}]}
    (d / f"{request_key(params)}.json").write_text(json.dumps({"content": "sai shape"}))
    with pytest.raises(Exception):
        c.create(**params)


@pytest.mark.parametrize("model,extra,needle", [
    ("claude-haiku-5-5", {"temperature": 0}, "temperature"),
    ("claude-sonnet-5-5", {"thinking": {"type": "enabled", "budget_tokens": 2000}}, "budget_tokens"),
    ("claude-opus-5-5", {"thinking": {"type": "disabled"}}, "tắt được thinking"),
    ("claude-sonnet-5-5", {"thinking": {"type": "disabled"}}, "between_tools"),
    ("claude-fable-5-1", {"tool_choice": {"type": "any"}}, "tool_choice"),
])
def test_rules_reject_like_api(model, extra, needle):
    params = {"model": model, "messages": [{"role": "user", "content": "x"}], **extra}
    with pytest.raises(ModelRuleError, match=needle):
        check_request(params)


def test_prefill_rejected():
    params = {"model": "claude-haiku-5-5", "messages": [
        {"role": "user", "content": "JSON?"}, {"role": "assistant", "content": "{"}]}
    with pytest.raises(ModelRuleError, match="Prefill"):
        check_request(params)


def test_unknown_and_retired_models():
    with pytest.raises(ModelRuleError, match="không có"):
        check_request({"model": "claude-haiku-4-5", "messages": []})
    with pytest.raises(ModelRuleError, match="ngừng"):
        check_request({"model": "claude-3-haiku-20240307", "messages": []})


def test_max_tokens_guard(mock_client):
    c, _ = mock_client
    with pytest.raises(ValueError, match="trần"):
        c.ask("x", max_tokens=100_000)


def test_cost_estimate(mock_client):
    c, _ = mock_client
    cost = estimate_cost_usd(c.ask("x"))
    assert cost == pytest.approx((12 * 0.10 + 18 * 0.50) / 1e6)


def test_stream_text_matches_final_message(mock_client):
    c, _ = mock_client
    with c.stream(messages=[{"role": "user", "content": "Xin chào"}]) as s:
        chunks = list(s.text_stream)
        msg = s.get_final_message()
    assert len(chunks) > 1                              # thật sự chia nhỏ, không trả một cục
    assert "".join(chunks) == text_of(msg)
    assert msg.content[0].type == "thinking"


def test_stream_events_follow_api_order(mock_client):
    c, _ = mock_client
    with c.stream(messages=[{"role": "user", "content": "x"}]) as s:
        types = [e.type for e in s]
    assert types[0] == "message_start" and types[-1] == "message_stop"
    assert types[-2] == "message_delta"
    assert types.count("content_block_start") == types.count("content_block_stop") == 2


def test_stream_uses_fixture_and_rules(mock_client):
    c, d = mock_client
    params = {"model": "claude-haiku-5-5", "messages": [{"role": "user", "content": "1+1?"}]}
    (d / f"{request_key(params)}.json").write_text(json.dumps({
        "id": "msg_x", "type": "message", "role": "assistant", "model": "claude-haiku-5-5",
        "content": [{"type": "text", "text": "Bằng 2, chắc chắn luôn."}], "stop_reason": "end_turn",
        "stop_sequence": None, "usage": {"input_tokens": 5, "output_tokens": 9},
    }))
    with c.stream(**params) as s:
        assert "".join(s.text_stream) == "Bằng 2, chắc chắn luôn."
    with pytest.raises(ModelRuleError, match="temperature"):
        c.stream(messages=[{"role": "user", "content": "x"}], temperature=0)


def test_small_max_tokens_truncates_like_api(mock_client):
    c, _ = mock_client
    full = c.ask("x")
    cut = c.ask("x", max_tokens=10)
    assert full.stop_reason == "end_turn" and cut.stop_reason == "max_tokens"
    assert cut.usage.output_tokens == 10
    assert text_of(full).startswith(text_of(cut)) and len(text_of(cut)) < len(text_of(full))
    assert full.usage.output_tokens_details.thinking_tokens <= full.usage.output_tokens


@pytest.mark.parametrize("status,exc", [
    (429, anthropic.RateLimitError),
    (529, anthropic.OverloadedError),
    (500, anthropic.InternalServerError),
    (400, anthropic.BadRequestError),
])
def test_mock_raises_sdk_errors(status, exc):
    s = Settings(model="claude-haiku-5-5", max_tokens=512, mock=True, record=False)
    c = ClaudeVi(settings=s, client=MockAnthropic(errors=[status]))
    with pytest.raises(exc) as info:
        c.ask("x")
    assert info.value.status_code == status and info.value.request_id == "req_mock"
    assert text_of(c.ask("x")).startswith("[MOCK]")    # lỗi chỉ xảy ra một lần


@pytest.mark.parametrize("model,extra,needle", [
    ("claude-haiku-5-5", {"thinking": {"type": "enabled"}}, "enabled"),
    ("claude-opus-5-5", {"thinking": {"type": "between_tools"}}, "chỉ có trên Sonnet"),
    ("claude-haiku-5-5", {"thinking": {"type": "disabled"}, "output_config": {"effort": "max"}}, "cần thinking"),
    ("claude-sonnet-5-5", {"thinking": {"type": "between_tools"}, "output_config": {"effort": "xhigh"}},
     "cần thinking"),
    ("claude-haiku-5-5", {"output_config": {"effort": "adaptive"}}, "chế độ thinking"),
    ("claude-haiku-5-5", {"output_config": {"format": {"type": "json"}}}, "json_schema"),
])
def test_thinking_effort_format_rules(model, extra, needle):
    params = {"model": model, "messages": [{"role": "user", "content": "x"}], **extra}
    with pytest.raises(ModelRuleError, match=needle):
        check_request(params)


def test_allowed_thinking_effort_combinations():
    for model, extra in [
        ("claude-haiku-5-5", {"thinking": {"type": "disabled"}, "output_config": {"effort": "high"}}),
        ("claude-sonnet-5-5", {"thinking": {"type": "between_tools"}}),
        ("claude-opus-5-5", {"thinking": {"type": "adaptive"}, "output_config": {"effort": "max"}}),
    ]:
        check_request({"model": model, "messages": [{"role": "user", "content": "x"}], **extra})


def test_schema_errors_like_structured_outputs():
    from claude_vi.rules import schema_errors

    ok = {"type": "object", "properties": {"n": {"type": "integer"}, "tags": {"type": "array",
          "items": {"type": "string"}}}, "required": ["n"], "additionalProperties": False}
    assert schema_errors(ok) == []
    bad = {"type": "object", "properties": {
        "n": {"type": "integer", "minimum": 0},
        "inner": {"type": "object", "properties": {"x": {"type": "string"}}},
        "tags": {"type": "array", "items": {"type": "string"}, "minItems": 2},
    }}
    errs = " | ".join(schema_errors(bad))
    assert "schema: object phải có additionalProperties" in errs
    assert "schema.inner: object phải có additionalProperties" in errs
    assert "'minimum'" in errs and "minItems" in errs


def test_mock_effort_changes_thinking_tokens(mock_client):
    c, _ = mock_client
    tokens = {e: c.ask("x", output_config={"effort": e}).usage.output_tokens_details.thinking_tokens
              for e in ("low", "medium", "high", "max")}
    assert tokens["low"] < tokens["medium"] < tokens["high"] < tokens["max"]
    assert c.ask("x").usage.output_tokens_details.thinking_tokens == tokens["medium"]   # mặc định Haiku 5.5
    off = c.ask("x", thinking={"type": "disabled"})
    assert [b.type for b in off.content] == ["text"]


def test_mock_structured_output_matches_schema(mock_client):
    c, _ = mock_client
    schema = {
        "type": "object",
        "properties": {
            "ghi_chu": {"type": "string"},
            "nhan": {"type": "string", "enum": ["tot", "xau"]},
            "diem": {"type": "integer"},
            "ngay": {"type": "string", "format": "date"},
            "the": {"type": "array", "items": {"$ref": "#/$defs/the"}},
        },
        "required": ["nhan", "diem", "ngay", "the"],
        "additionalProperties": False,
        "$defs": {"the": {"type": "object", "properties": {"ten": {"type": "string"}},
                          "required": ["ten"], "additionalProperties": False}},
    }
    msg = c.ask("x", output_config={"format": {"type": "json_schema", "schema": schema}})
    data = json.loads(text_of(msg))
    assert list(data) == ["nhan", "diem", "ngay", "the", "ghi_chu"]      # required trước
    assert data["nhan"] == "tot" and data["diem"] == 0 and data["ngay"] == "2026-01-01"
    assert data["the"] == [{"ten": "[MOCK]"}]


TOOL = {
    "name": "tra_aqi",
    "description": "Tra chỉ số AQI hiện tại của một thành phố.",
    "strict": True,
    "input_schema": {"type": "object", "properties": {"thanh_pho": {"type": "string", "enum": ["Hà Nội", "Huế"]}},
                     "required": ["thanh_pho"], "additionalProperties": False},
}
TOOL2 = {**TOOL, "name": "tra_gio"}


def test_tool_definition_rules():
    base = {"model": "claude-haiku-5-5", "messages": [{"role": "user", "content": "x"}]}
    with pytest.raises(ModelRuleError, match="Tên tool"):
        check_request({**base, "tools": [{**TOOL, "name": "tra cứu"}]})
    loose = {**TOOL, "input_schema": {"type": "object", "properties": {"q": {"type": "string"}}}}
    with pytest.raises(ModelRuleError, match="strict.*additionalProperties"):
        check_request({**base, "tools": [loose]})
    check_request({**base, "tools": [{**loose, "strict": False}]})          # không strict thì không bắt buộc
    with pytest.raises(ModelRuleError, match="Tối đa 20"):
        check_request({**base, "tools": [{**TOOL, "name": f"t{i}"} for i in range(21)]})


def test_tool_loop_in_mock(mock_client):
    c, _ = mock_client
    msgs = [{"role": "user", "content": "AQI Hà Nội?"}]
    first = c.create(messages=msgs, tools=[TOOL])
    assert first.stop_reason == "tool_use"
    assert [b.type for b in first.content] == ["thinking", "text", "tool_use"]
    call = first.content[-1]
    assert call.input == {"thanh_pho": "Hà Nội"}

    msgs += [{"role": "assistant", "content": first.content},
             {"role": "user", "content": [{"type": "tool_result", "tool_use_id": call.id, "content": "AQI 152"}]}]
    final = c.create(messages=msgs, tools=[TOOL])
    assert final.stop_reason == "end_turn" and "AQI 152" in text_of(final)


def test_parallel_and_tool_choice(mock_client):
    c, _ = mock_client
    msgs = [{"role": "user", "content": "x"}]
    both = c.create(messages=msgs, tools=[TOOL, TOOL2])
    assert [b.name for b in both.content if b.type == "tool_use"] == ["tra_aqi", "tra_gio"]
    one = c.create(messages=msgs, tools=[TOOL, TOOL2], tool_choice={"type": "auto", "disable_parallel_tool_use": True})
    assert [b.type for b in one.content].count("tool_use") == 1
    none = c.create(messages=msgs, tools=[TOOL], tool_choice={"type": "none"})
    assert none.stop_reason == "end_turn"


def test_tool_result_rules(mock_client):
    c, _ = mock_client
    first = c.create(messages=[{"role": "user", "content": "x"}], tools=[TOOL, TOOL2])
    ids = [b.id for b in first.content if b.type == "tool_use"]
    head = [{"role": "user", "content": "x"}, {"role": "assistant", "content": first.content}]

    def result(i):
        return {"type": "tool_result", "tool_use_id": i, "content": "ok"}

    with pytest.raises(ModelRuleError, match="without tool_result"):          # thiếu một kết quả
        c.create(messages=[*head, {"role": "user", "content": [result(ids[0])]}], tools=[TOOL, TOOL2])
    with pytest.raises(ModelRuleError, match="ĐẦU content"):                  # text đứng trước tool_result
        c.create(messages=[*head, {"role": "user", "content": [
            {"type": "text", "text": "kết quả:"}, result(ids[0]), result(ids[1])]}], tools=[TOOL, TOOL2])
    ok = c.create(messages=[*head, {"role": "user", "content": [
        result(ids[0]), result(ids[1]), {"type": "text", "text": "tóm tắt giúp"}]}], tools=[TOOL, TOOL2])
    assert ok.stop_reason == "end_turn"


def test_stripping_thinking_in_tool_loop_is_400(mock_client):
    c, _ = mock_client
    first = c.create(messages=[{"role": "user", "content": "x"}], tools=[TOOL])
    call = first.content[-1]
    stripped = [b for b in first.content if b.type != "thinking"]
    with pytest.raises(anthropic.BadRequestError, match="cannot be modified"):
        c.create(tools=[TOOL], messages=[
            {"role": "user", "content": "x"}, {"role": "assistant", "content": stripped},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": call.id, "content": "ok"}]}])


def test_forced_tool_choice_skips_thinking(mock_client):
    c, _ = mock_client
    msg = c.create(messages=[{"role": "user", "content": "x"}], tools=[TOOL],
                   tool_choice={"type": "tool", "name": "tra_aqi"})
    assert [b.type for b in msg.content] == ["tool_use"]


def test_stream_tool_use(mock_client):
    c, _ = mock_client
    with c.stream(messages=[{"role": "user", "content": "x"}], tools=[TOOL]) as s:
        msg = s.get_final_message()
    assert msg.content[-1].type == "tool_use"


def _pdf_doc():
    import base64
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "capstones/c2-trich-xuat-pdf/data/tao_pdf_mau.py"
    spec = importlib.util.spec_from_file_location("tao_pdf_mau", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    data = base64.b64encode(mod.build_pdf()).decode()
    return {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": data},
            "title": "Báo cáo", "citations": {"enabled": True}}


def test_mock_pdf_citations_have_page_numbers(mock_client):
    c, _ = mock_client
    msg = c.create(messages=[{"role": "user", "content": [_pdf_doc(), {"type": "text", "text": "Trích số liệu"}]}])
    cits = [cit for b in msg.content if b.type == "text" for cit in (b.citations or [])]
    assert cits and all(cit.type == "page_location" for cit in cits)
    by_page = {cit.start_page_number for cit in cits}
    assert by_page == {1, 2}
    a1 = next(cit for cit in cits if cit.cited_text.startswith("Specimen A1"))
    assert a1.start_page_number == 1 and a1.end_page_number == 2 and "276 MPa" in a1.cited_text


def test_mock_text_citations_char_location(mock_client):
    c, _ = mock_client
    data = "Mẫu nước sạch. Mẫu W1 có pH 7.1 và DO 6.2 mg/L. Hết."
    doc = {"type": "document", "source": {"type": "text", "media_type": "text/plain", "data": data},
           "citations": {"enabled": True}}
    msg = c.create(messages=[{"role": "user", "content": [doc, {"type": "text", "text": "?"}]}])
    cit = next(cit for b in msg.content if b.type == "text" for cit in (b.citations or []))
    assert cit.type == "char_location"
    assert data[cit.start_char_index:cit.end_char_index] == cit.cited_text == "Mẫu W1 có pH 7.1 và DO 6.2 mg/L."


def test_citations_and_structured_outputs_conflict():
    params = {"model": "claude-haiku-5-5", "messages": [{"role": "user", "content": [_pdf_doc()]}],
              "output_config": {"format": {"type": "json_schema", "schema": {
                  "type": "object", "properties": {}, "additionalProperties": False}}}}
    with pytest.raises(ModelRuleError, match="không dùng chung"):
        check_request(params)


def _text_doc(data, enabled=True):
    return {"type": "document", "source": {"type": "text", "media_type": "text/plain", "data": data},
            "citations": {"enabled": enabled}}


def test_citations_all_or_none():
    base = {"model": "claude-haiku-5-5"}
    mixed = [{"role": "user", "content": [_text_doc("A 1 2."), _text_doc("B 3 4.", enabled=False)]}]
    with pytest.raises(ModelRuleError, match="tất cả hoặc không"):
        check_request({**base, "messages": mixed})
    check_request({**base, "messages": [{"role": "user", "content": [_text_doc("A."), _text_doc("B.")]}]})


def test_mock_custom_content_citations(mock_client):
    c, _ = mock_client
    doc = {"type": "document", "title": "Nhật ký", "citations": {"enabled": True}, "source": {"type": "content",
           "content": [{"type": "text", "text": "- Mở máy lúc 8 giờ"}, {"type": "text", "text": "- W1: pH 7,1; DO 6,2"}]}}
    msg = c.create(messages=[{"role": "user", "content": [doc, {"type": "text", "text": "?"}]}])
    cit = next(cit for b in msg.content if b.type == "text" for cit in (b.citations or []))
    assert cit.type == "content_block_location"
    assert (cit.start_block_index, cit.end_block_index) == (1, 2) and "pH 7,1" in cit.cited_text


def test_stream_carries_citations(mock_client):
    c, _ = mock_client
    data = "Mẫu W1 có pH 7.1 và DO 6.2 mg/L."
    with c.stream(messages=[{"role": "user", "content": [_text_doc(data), {"type": "text", "text": "?"}]}]) as s:
        deltas = [e.delta for e in s if e.type == "content_block_delta" and e.delta.type == "citations_delta"]
    assert len(deltas) == 1 and deltas[0].citation.cited_text == data


def test_schema_complexity_limits():
    from claude_vi.rules import count_params

    def obj(n_opt, union=False):
        typ = {"type": ["string", "null"]} if union else {"type": "string"}
        return {"type": "object", "properties": {f"p{i}": typ for i in range(n_opt)}, "required": [],
                "additionalProperties": False}

    assert count_params(obj(3, union=True)) == (3, 3)
    fmt = {"type": "json_schema", "schema": obj(20)}
    base = {"model": "claude-haiku-5-5", "messages": [{"role": "user", "content": "x"}]}
    check_request({**base, "output_config": {"format": fmt}})
    tool = {**TOOL, "input_schema": obj(5)}
    with pytest.raises(ModelRuleError, match="25 tham số optional"):         # gộp output schema + tool strict
        check_request({**base, "output_config": {"format": fmt}, "tools": [tool]})
    check_request({**base, "output_config": {"format": fmt}, "tools": [{**tool, "strict": False}]})
    with pytest.raises(ModelRuleError, match="17 tham số dùng anyOf"):
        check_request({**base, "output_config": {"format": {"type": "json_schema", "schema": obj(17, union=True)}}})


@pytest.mark.parametrize("pattern,ok", [(r"^\d{4}-\d{2}$", True), (r"^(a)\1$", False),
                                        (r"^(?=.*\d).+$", False), (r"\bpH\b", False)])
def test_schema_pattern_support(pattern, ok):
    from claude_vi.rules import schema_errors

    errs = schema_errors({"type": "string", "pattern": pattern})
    assert (errs == []) is ok
