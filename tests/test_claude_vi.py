import json

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
