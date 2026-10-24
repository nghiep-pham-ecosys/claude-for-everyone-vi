"""Test model_sync bằng response giả lập — không gọi mạng.

tests/fixtures/models_list.json là dữ liệu BỊA theo shape của GET /v1/models (2 trang),
không phải dữ kiện thật về model. claude-test-new-9-9 là model không tồn tại.
"""
import json
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

import model_sync as ms

FIXTURE = Path(__file__).parent / "fixtures" / "models_list.json"

LOCAL_YAML = """\
# comment đầu file phải còn sau --write
default_model: claude-haiku-5-5

models:
  claude-opus-5-5:
    status: active
    price_per_mtok: {input: 4.0, output: 20.0}
    rules:
      thinking_disabled_allowed: false    # 2026-09-22

  claude-haiku-5-5:
    status: active
    rules:
      thinking_disabled_allowed: false    # giả định sai, API nói true

  claude-sonnet-4-5-20250929:
    status: active                        # API nói deprecated
    retire_on: 2026-11-30

  claude-gone-1-0:
    status: active
"""


@pytest.fixture
def local_file(tmp_path):
    p = tmp_path / "models.yaml"
    p.write_text(LOCAL_YAML, "utf-8")
    return p


def remote():
    return [ms.summarize(m) for m in ms.fetch_all(ms.fixture_fetcher(FIXTURE))]


def test_pagination_follows_last_id():
    calls = []
    inner = ms.fixture_fetcher(FIXTURE)

    def spy(after_id):
        calls.append(after_id)
        return inner(after_id)

    models = ms.fetch_all(spy)
    first_page = json.loads(FIXTURE.read_text("utf-8"))[0]
    assert calls == [None, first_page["last_id"]]
    assert len(models) == 7


def test_pagination_stops_on_stuck_cursor():
    with pytest.raises(RuntimeError, match="không tiến"):
        ms.fetch_all(lambda after_id: ([], True, "same"))


def test_fixture_is_validated_by_sdk_types(tmp_path):
    pages = json.loads(FIXTURE.read_text("utf-8"))
    pages[0]["data"][0]["lifecycle"] = "sắp-chết"
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(pages), "utf-8")
    with pytest.raises(ValidationError):
        ms.fetch_all(ms.fixture_fetcher(bad))


def test_summarize_reads_capabilities():
    by_id = {r.id: r for r in remote()}
    haiku = by_id["claude-haiku-5-5"]
    assert haiku.thinking_disabled is True
    assert haiku.server_tools == ["web_search"]
    assert haiku.max_tokens == 32000
    assert by_id["claude-3-haiku-20240307"].server_tools == []


def test_compare_finds_every_kind_of_drift(local_file):
    rep = ms.compare(yaml.safe_load(local_file.read_text("utf-8")), remote())
    assert rep.new == ["claude-fable-5-1", "claude-sonnet-5-5", "claude-test-new-9-9"]
    assert "claude-3-haiku-20240307" not in rep.new        # retired: không coi là model mới
    assert rep.missing == ["claude-gone-1-0"]
    assert rep.thinking == [("claude-haiku-5-5", False, True)]
    assert rep.lifecycle == [("claude-sonnet-4-5-20250929", "active", "deprecated")]
    assert ("claude-opus-5-5", "max_tokens", None, 128000) in rep.info
    assert rep.drift


def test_write_preserves_comments_and_is_idempotent(local_file):
    rep = ms.compare(yaml.safe_load(local_file.read_text("utf-8")), remote())
    ms.apply(rep, local_file)
    text = local_file.read_text("utf-8")

    assert text.startswith("# comment đầu file phải còn sau --write")
    assert "thinking_disabled_allowed: false    # 2026-09-22" in text   # dòng không đổi giữ nguyên
    assert "giả định sai" not in text                                  # comment lỗi thời bị thay
    assert "server_tools: [code_execution, web_search]" in text

    data = yaml.safe_load(text)
    assert data["models"]["claude-haiku-5-5"]["rules"]["thinking_disabled_allowed"] is True
    assert data["models"]["claude-sonnet-4-5-20250929"]["status"] == "deprecated"
    assert list(data["models"]["claude-opus-5-5"])[:3] == ["status", "max_tokens", "server_tools"]
    assert "claude-test-new-9-9" not in data["models"]                 # không tự thêm model
    assert "claude-gone-1-0" in data["models"]                         # không tự xoá model

    again = ms.compare(data, remote())
    assert again.thinking == again.lifecycle == again.info == []


def test_main_exit_codes(local_file, monkeypatch, capsys):
    opened = []
    monkeypatch.setattr(ms, "open_issue", opened.append)
    args = ["--fixture", str(FIXTURE), "--models-file", str(local_file)]

    assert ms.main(args) == 1
    assert opened == []                                     # không --issue thì không mở issue
    assert ms.main([*args, "--write", "--issue"]) == 1      # còn model mới / biến mất
    assert len(opened) == 1 and "claude-gone-1-0" in opened[0]
    assert "model-sync" in capsys.readouterr().out


def test_main_clean_when_yaml_matches(tmp_path):
    models = {}
    for r in remote():
        models[r.id] = {"status": r.lifecycle, "rules": {"thinking_disabled_allowed": r.thinking_disabled}}
        if r.lifecycle != "retired":
            models[r.id] |= {"max_tokens": r.max_tokens, "server_tools": r.server_tools}
    p = tmp_path / "models.yaml"
    p.write_text(yaml.safe_dump({"models": models}), "utf-8")
    assert ms.main(["--fixture", str(FIXTURE), "--models-file", str(p)]) == 0


def test_open_issue_builds_gh_command():
    seen = []
    ms.open_issue("body", run=lambda cmd, check: seen.append((cmd, check)))
    cmd, check = seen[0]
    assert cmd[:3] == ["gh", "issue", "create"] and cmd[-1] == "body" and check
