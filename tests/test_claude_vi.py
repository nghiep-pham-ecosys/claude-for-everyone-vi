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


# ---------- Thinking: display, redacted, prefix check, message system giữa hội thoại ----------

def test_display_summarized_returns_text_but_same_billing(mock_client):
    c, _ = mock_client
    an = c.ask("x")
    hien = c.ask("x", thinking={"type": "adaptive", "display": "summarized"})
    assert an.content[0].thinking == "" and hien.content[0].thinking.startswith("[MOCK]")
    assert an.usage.output_tokens == hien.usage.output_tokens          # tóm tắt không làm đổi số token bị tính
    assert an.content[0].signature != hien.content[0].signature        # mỗi block một chữ ký


@pytest.mark.parametrize("model,thinking,needle", [
    ("claude-haiku-5-5", {"type": "disabled", "display": "omitted"}, "không có gì để hiển thị"),
    ("claude-sonnet-5-5", {"type": "between_tools", "display": "summarized"}, "không nhận trường nào khác"),
    ("claude-haiku-5-5", {"type": "adaptive", "display": "updates"}, "beta"),
    ("claude-haiku-5-5", {"type": "adaptive", "display": "full"}, "summarized"),
    ("claude-haiku-5-5", {"type": "auto"}, "thinking.type"),
    ("claude-opus-5-5", {"type": "adaptive", "block_binding": {"prefix_mismatch_behavior": "drop_block"}}, "beta"),
])
def test_thinking_shape_rules(model, thinking, needle):
    with pytest.raises(ModelRuleError, match=needle):
        check_request({"model": model, "messages": [{"role": "user", "content": "x"}], "thinking": thinking})


def test_redacted_thinking_must_be_kept_in_tool_loop(tmp_path):
    s = Settings(model="claude-haiku-5-5", max_tokens=512, mock=True, record=False)
    c = ClaudeVi(settings=s, client=MockAnthropic(record_dir=tmp_path, redacted=True))
    first = c.create(messages=[{"role": "user", "content": "x"}], tools=[TOOL])
    assert [b.type for b in first.content] == ["thinking", "redacted_thinking", "text", "tool_use"]
    call = first.content[-1]
    result = {"role": "user", "content": [{"type": "tool_result", "tool_use_id": call.id, "content": "ok"}]}
    chi_thinking = [b for b in first.content if b.type != "redacted_thinking"]     # lọc theo type == "thinking"
    with pytest.raises(anthropic.BadRequestError, match="cannot be modified"):
        c.create(tools=[TOOL], messages=[{"role": "user", "content": "x"},
                                         {"role": "assistant", "content": chi_thinking}, result])
    ok = c.create(tools=[TOOL], messages=[{"role": "user", "content": "x"},
                                          {"role": "assistant", "content": first.content}, result])
    assert ok.stop_reason == "end_turn"
    with c.stream(messages=[{"role": "user", "content": "y"}]) as st:
        assert [b.type for b in st.get_final_message().content][:2] == ["thinking", "redacted_thinking"]


def test_summarized_thinking_must_not_be_edited(mock_client):
    c, _ = mock_client
    cfg = {"type": "adaptive", "display": "summarized"}
    first = c.create(messages=[{"role": "user", "content": "x"}], tools=[TOOL], thinking=cfg)
    sua = [b.model_copy(update={"thinking": "đã sửa"}) if b.type == "thinking" else b for b in first.content]
    result = {"role": "user", "content": [{"type": "tool_result", "tool_use_id": first.content[-1].id,
                                           "content": "ok"}]}
    with pytest.raises(anthropic.BadRequestError, match="cannot be modified"):
        c.create(tools=[TOOL], thinking=cfg, messages=[{"role": "user", "content": "x"},
                                                       {"role": "assistant", "content": sua}, result])


def _hai_luot(c, system1, system2, them=None):
    u1 = {"role": "user", "content": "Câu 1"}
    a1 = c.create(system=system1, messages=[u1])
    msgs = [u1, {"role": "assistant", "content": a1.content}, {"role": "user", "content": "Câu 2"}, *(them or [])]
    return c.create(system=system2, messages=msgs)


def test_prefix_check_edit_system_is_400(mock_client):
    c, _ = mock_client
    with pytest.raises(anthropic.BadRequestError, match="bound to a different conversation.*`system` prompt"):
        _hai_luot(c, "Trả lời ngắn.", "Trả lời ngắn. Hôm nay là thứ Hai.")
    assert _hai_luot(c, "Trả lời ngắn.", "Trả lời ngắn.").stop_reason == "end_turn"


def test_prefix_check_edit_earlier_message_or_tools(mock_client):
    c, _ = mock_client
    u1 = {"role": "user", "content": "Câu 1"}
    a1 = c.create(messages=[u1])
    with pytest.raises(anthropic.BadRequestError, match="An earlier message"):
        c.create(messages=[{"role": "user", "content": "Câu 1 (sửa)"}, {"role": "assistant", "content": a1.content},
                           {"role": "user", "content": "Câu 2"}])
    with pytest.raises(anthropic.BadRequestError, match="`tools` list"):
        c.create(tools=[TOOL], tool_choice={"type": "none"},
                 messages=[u1, {"role": "assistant", "content": a1.content}, {"role": "user", "content": "Câu 2"}])
    # bỏ block thinking cũ (không thuộc prefix) thì được
    bo = [b for b in a1.content if b.type != "thinking"]
    c.create(messages=[u1, {"role": "assistant", "content": bo}, {"role": "user", "content": "Câu 2"}])


def test_mid_conversation_system_keeps_prefix(mock_client):
    c, _ = mock_client
    them = [{"role": "system", "content": "Từ giờ trả lời bằng tiếng Anh."}]
    assert _hai_luot(c, "Trả lời ngắn.", "Trả lời ngắn.", them).stop_reason == "end_turn"


@pytest.mark.parametrize("msgs,needle", [
    ([{"role": "system", "content": "a"}, {"role": "user", "content": "x"}], "không được đứng đầu"),
    ([{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"}, {"role": "system", "content": "a"},
      {"role": "user", "content": "z"}], "ngay sau một lượt user"),
    ([{"role": "user", "content": "x"}, {"role": "system", "content": "a"}, {"role": "user", "content": "z"}],
     "phải là lượt assistant"),
    ([{"role": "user", "content": "x"}, {"role": "system", "content": [], "output_config": {"effort": "low"}}],
     "beta"),
])
def test_mid_conversation_system_placement(msgs, needle):
    with pytest.raises(ModelRuleError, match=needle):
        check_request({"model": "claude-haiku-5-5", "messages": msgs})


def test_fable_5_2_rules():
    base = {"model": "claude-fable-5-2", "messages": [{"role": "user", "content": "x"}]}
    check_request(base)
    with pytest.raises(ModelRuleError, match="Không tắt được"):
        check_request({**base, "thinking": {"type": "disabled"}})
    with pytest.raises(ModelRuleError, match="tool_choice"):
        check_request({**base, "tools": [TOOL], "tool_choice": {"type": "any"}})


# ---------- search_result (RAG) ----------

def _sr(source, *texts, enabled=True):
    return {"type": "search_result", "source": source, "title": source.split("/")[-1],
            "content": [{"type": "text", "text": t} for t in texts], "citations": {"enabled": enabled}}


def test_mock_search_result_citations_top_level(mock_client):
    c, _ = mock_client
    msg = c.create(messages=[{"role": "user", "content": [
        _sr("kb://a", "Máy đo pH hiệu chuẩn mỗi ngày.", "Lỗi E-17 nghĩa là điện cực khô."),
        _sr("kb://b", "Mẫu nước bảo quản ở 4 °C."),
        {"type": "text", "text": "Lỗi E-17 là gì?"}]}])
    cits = [cit for b in msg.content if b.type == "text" for cit in (b.citations or [])]
    assert cits[0].type == "search_result_location"
    assert (cits[0].source, cits[0].search_result_index, cits[0].start_block_index, cits[0].end_block_index) == \
        ("kb://a", 0, 1, 2)
    assert cits[0].cited_text == "Lỗi E-17 nghĩa là điện cực khô."


def test_mock_search_result_from_tool(mock_client):
    c, _ = mock_client
    tool = {"name": "tim", "description": "Tìm trong sổ tay.", "input_schema": {
        "type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"], "additionalProperties": False}}
    u = {"role": "user", "content": "Bảo quản mẫu nước thế nào?"}
    first = c.create(messages=[u], tools=[tool])
    call = first.content[-1]
    kq = {"role": "user", "content": [{"type": "tool_result", "tool_use_id": call.id, "content": [
        _sr("kb://a", "Máy đo pH hiệu chuẩn mỗi ngày."), _sr("kb://b", "Mẫu nước bảo quản ở 4 °C.")]}]}
    final = c.create(messages=[u, {"role": "assistant", "content": first.content}, kq], tools=[tool])
    cit = next(cit for b in final.content if b.type == "text" for cit in (b.citations or []))
    assert (cit.source, cit.search_result_index) == ("kb://b", 1)


@pytest.mark.parametrize("content,needle", [
    ([_sr("kb://a", "x"), _sr("kb://b", "y", enabled=False)], "tất cả hoặc không"),
    ([{**_sr("kb://a", "x"), "source": ""}], "cần source"),
    ([{**_sr("kb://a", "x"), "content": []}], "không rỗng"),
    ([_sr("kb://a", "")], "có chữ"),
])
def test_search_result_rules(content, needle):
    with pytest.raises(ModelRuleError, match=needle):
        check_request({"model": "claude-haiku-5-5", "messages": [{"role": "user", "content": content}]})


def test_search_result_rules_in_tool_result_and_assistant():
    base = {"model": "claude-haiku-5-5"}
    tu = {"role": "assistant", "content": [{"type": "tool_use", "id": "t1", "name": "tim", "input": {}}]}
    tron = {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": [
        _sr("kb://a", "x"), {"type": "text", "text": "ghi chú"}]}]}
    with pytest.raises(ModelRuleError, match="mọi block bên trong"):
        check_request({**base, "messages": [{"role": "user", "content": "q"}, tu, tron]})
    with pytest.raises(ModelRuleError, match="chỉ được đặt trong lượt user"):
        check_request({**base, "messages": [{"role": "user", "content": "q"},
                                            {"role": "assistant", "content": [_sr("kb://a", "x")]},
                                            {"role": "user", "content": "tiếp"}]})


# ---------- mock cho module 08 (agent nhiều bước, router, nhiều luồng) ----------

def _agent(c, tools, cau_hoi="AQI và giờ ở Huế?", max_luot=10):
    """Vòng lặp agent tối thiểu: chạy tới khi hết tool_use, trả (số lượt, các tool đã gọi, message cuối)."""
    msgs, goi = [{"role": "user", "content": cau_hoi}], []
    for luot in range(1, max_luot + 1):
        msg = c.create(messages=msgs, tools=tools)
        if msg.stop_reason != "tool_use":
            return luot, goi, msg
        uses = [b for b in msg.content if b.type == "tool_use"]
        goi.append([b.name for b in uses])
        msgs += [{"role": "assistant", "content": msg.content}, {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": b.id, "content": f"kết quả {b.name}"} for b in uses]}]
    raise AssertionError("agent không dừng")


def test_multi_step_calls_one_tool_per_turn(tmp_path):
    s = Settings(model="claude-haiku-5-5", max_tokens=512, mock=True, record=False)
    c = ClaudeVi(settings=s, client=MockAnthropic(record_dir=tmp_path, multi_step=True))
    luot, goi, final = _agent(c, [TOOL, TOOL2])
    assert goi == [["tra_aqi"], ["tra_gio"]] and luot == 3       # mỗi lượt một tool, theo thứ tự trong tools
    assert final.stop_reason == "end_turn"
    assert "kết quả tra_aqi" in text_of(final) and "kết quả tra_gio" in text_of(final)


def test_multi_step_off_by_default(mock_client):
    c, _ = mock_client
    luot, goi, _final = _agent(c, [TOOL, TOOL2])
    assert goi == [["tra_aqi", "tra_gio"]] and luot == 2         # hành vi module 03 giữ nguyên


def test_multi_step_answers_once_every_tool_has_a_result(tmp_path):
    s = Settings(model="claude-haiku-5-5", max_tokens=512, mock=True, record=False)
    c = ClaudeVi(settings=s, client=MockAnthropic(record_dir=tmp_path, multi_step=True))
    u = {"role": "user", "content": "AQI Hà Nội?"}
    first = c.create(messages=[u], tools=[TOOL, TOOL2])
    call = first.content[-1]
    msgs = [u, {"role": "assistant", "content": first.content}, {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": call.id, "content": "AQI 152"}]}]
    second = c.create(messages=msgs, tools=[TOOL, TOOL2])
    assert [b.name for b in second.content if b.type == "tool_use"] == ["tra_gio"]
    msgs += [{"role": "assistant", "content": second.content}, {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": second.content[-1].id, "content": "10:00"}]}]
    third = c.create(messages=msgs, tools=[TOOL, TOOL2])
    msgs += [{"role": "assistant", "content": third.content}, {"role": "user", "content": "Tóm tắt lại giúp mình."}]
    # Mọi tool đã có kết quả: câu hỏi tiếp theo được trả lời, không gọi lại tool
    again = c.create(messages=msgs, tools=[TOOL, TOOL2])
    assert again.stop_reason == "end_turn"
    assert "AQI 152" in text_of(again) and "10:00" in text_of(again)


ROUTER = {"type": "object", "properties": {"nhan": {"type": "string", "enum": ["quy_trinh", "so_lieu", "khac"]}},
          "required": ["nhan"], "additionalProperties": False}


@pytest.mark.parametrize("cau_hoi,nhan", [
    ("Số liệu cảm biến hôm qua là bao nhiêu?", "so_lieu"),     # có dấu, khác hoa thường, "_" thành khoảng trắng
    ("Quy trình hiệu chuẩn máy đo pH?", "quy_trinh"),
    ("Hôm nay trời đẹp không?", "quy_trinh"),                  # không khớp từ khoá nào: phần tử đầu
    ("Câu này khác hẳn", "khac"),
    ("Khắc phục lỗi E-17", "khac"),                             # "khắc" bỏ dấu là "khac": mock không hiểu nghĩa
])
def test_structured_enum_follows_last_user_turn(mock_client, cau_hoi, nhan):
    c, _ = mock_client
    msg = c.ask(cau_hoi, output_config={"format": {"type": "json_schema", "schema": ROUTER}})
    assert json.loads(text_of(msg))["nhan"] == nhan


def test_enum_hint_uses_last_user_text_and_nested_schema(mock_client):
    c, _ = mock_client
    schema = {"type": "object", "properties": {"buoc": {"type": "array", "items": {"$ref": "#/$defs/b"}},
                                               "dat": {"type": "boolean"}},
              "required": ["buoc", "dat"], "additionalProperties": False,
              "$defs": {"b": {"type": "object", "properties": {"loai": {"enum": ["doc", "ghi"]}},
                              "required": ["loai"], "additionalProperties": False}}}
    msgs = [{"role": "user", "content": "đọc sổ tay"}, {"role": "assistant", "content": "ok"},
            {"role": "user", "content": [{"type": "text", "text": "giờ ghi nhật ký"}]}]
    data = json.loads(text_of(c.create(messages=msgs, output_config={"format": {"type": "json_schema",
                                                                                "schema": schema}})))
    assert data == {"buoc": [{"loai": "ghi"}], "dat": False}  # boolean vẫn false: evaluator không bao giờ "đạt"


def test_tool_input_enum_unchanged(mock_client):
    c, _ = mock_client
    msg = c.create(messages=[{"role": "user", "content": "AQI Huế?"}], tools=[TOOL])
    assert msg.content[-1].input == {"thanh_pho": "Hà Nội"}     # chỉ structured outputs dò từ khoá


def test_mock_shared_between_threads(tmp_path):
    import sys
    from concurrent.futures import ThreadPoolExecutor

    mock = MockAnthropic(record_dir=tmp_path)
    s = Settings(model="claude-haiku-5-5", max_tokens=512, mock=True, record=False)
    c = ClaudeVi(settings=s, client=mock)

    def mot_luot(i):
        msg = c.create(messages=[{"role": "user", "content": f"câu {i}"}], tools=[TOOL, TOOL2])
        return [b.id for b in msg.content if b.type == "tool_use"], [b.signature for b in msg.content
                                                                   if b.type == "thinking"]

    old = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)                                 # đổi luồng thật dày để lộ tranh chấp nếu có
    try:
        with ThreadPoolExecutor(max_workers=8) as pool:
            ket_qua = list(pool.map(mot_luot, range(200)))
    finally:
        sys.setswitchinterval(old)
    ids = [i for ids, _ in ket_qua for i in ids]
    sigs = [x for _, sig in ket_qua for x in sig]
    assert mock.messages.calls == 200
    assert len(ids) == 400 and len(set(ids)) == 400              # không trùng id tool_use
    assert len(sigs) == 200 and len(set(sigs)) == 200            # không trùng chữ ký thinking
