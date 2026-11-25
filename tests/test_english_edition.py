"""Bản tiếng Anh (en/) phải phản chiếu đúng module tiếng Việt: cùng mục, cùng ví dụ, cùng nguồn.

Mỗi thư mục en/modules/NN-ten/ được so với modules/NN-ten/:
- cùng các file .md ở gốc module, cùng cấu trúc tiêu đề, cùng số câu quiz, cùng link ngoài;
- link tương đối trong README trỏ tới cùng file ví dụ (bản tiếng Anh nằm cùng đường dẫn dưới en/);
- bản tiếng Anh của script hoặc bài tập có file tiếng Việt cùng tên; bài tập giữ nguyên tên hàm, lớp, tham số
  (cùng bộ test chấm cả hai), và mọi bài tập tiếng Việt đều có bản tiếng Anh;
- mọi script tiếng Anh chạy được ở mock mode.
Không gọi mạng.
"""
from __future__ import annotations

import ast
import os
import posixpath
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EN = ROOT / "en"
EN_MODULES = sorted(p.name for p in (EN / "modules").iterdir() if p.is_dir())
EN_SCRIPTS = sorted((EN / "modules").glob("*/python/*.py"))

LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
URL = re.compile(r"https?://[^\s)>\]]+")
HEADING = re.compile(r"^(#{1,6})\s", re.MULTILINE)
QUESTION = re.compile(r"^\*\*\d+\.\*\*", re.MULTILINE)
TABLE_ROW = re.compile(r"^\|", re.MULTILINE)


def _read(path: Path) -> str:
    return path.read_text("utf-8")


def _no_code(text: str) -> str:
    """Bỏ khối code ```...``` để dấu # trong code không bị đếm là tiêu đề."""
    return re.sub(r"^```.*?^```", "", text, flags=re.MULTILINE | re.DOTALL)


def _local_targets(readme: Path) -> set[str]:
    """Đích của link tương đối, tính từ gốc repo; đích nằm dưới en/ được quy về đường dẫn tiếng Việt."""
    base = readme.parent.relative_to(ROOT).as_posix()
    out = set()
    for url in LINK.findall(_read(readme)):
        if re.match(r"^[a-z][a-z0-9+.-]*:", url) or url.startswith("#"):
            continue
        path = posixpath.normpath(posixpath.join(base, url.partition("#")[0]))
        assert (ROOT / path).exists(), f"{readme.relative_to(ROOT)}: link hỏng {url}"
        out.add(path.removeprefix("en/"))
    return out


def _args(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    a = fn.args
    star = [f"*{a.vararg.arg}"] if a.vararg else []
    return [x.arg for x in a.posonlyargs + a.args] + star + [x.arg for x in a.kwonlyargs]


def _api(path: Path) -> dict[str, list[str]]:
    """Tên hàm/lớp/phương thức cấp cao nhất kèm tên tham số."""
    api: dict[str, list[str]] = {}
    for node in ast.parse(_read(path)).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            api[node.name] = _args(node)
        elif isinstance(node, ast.ClassDef):
            api[node.name] = [n.target.id for n in node.body if isinstance(n, ast.AnnAssign)]
            for m in node.body:
                if isinstance(m, ast.FunctionDef):
                    api[f"{node.name}.{m.name}"] = _args(m)
    return api


def test_english_modules_exist():
    assert EN_MODULES, "en/modules/ chưa có module nào"


def test_modules_00_to_10_have_an_english_edition():
    """Bản tiếng Anh đã phủ cả khoá 00–10 (issue #4); module mới có thể ra tiếng Việt trước."""
    vi = sorted(p.name for p in (ROOT / "modules").iterdir() if p.is_dir() and p.name[:2] <= "10")
    assert len(vi) == 11, vi
    assert [m for m in vi if m not in EN_MODULES] == []


def test_language_switch_both_ways():
    assert "[English](en/README.md)" in _read(ROOT / "README.md")
    assert "[Tiếng Việt](../README.md)" in _read(EN / "README.md")


def test_english_readme_keeps_disclaimer():
    text = _read(EN / "README.md")
    assert "**unofficial**" in text
    assert "not affiliated with or endorsed by Anthropic" in text


def test_english_readme_lists_every_english_module():
    text = _read(EN / "README.md")
    for slug in EN_MODULES:
        assert f"(modules/{slug}/README.md)" in text, slug


@pytest.mark.parametrize("slug", EN_MODULES)
def test_module_exists_in_vietnamese(slug):
    assert (ROOT / "modules" / slug / "README.md").is_file()


@pytest.mark.parametrize("slug", EN_MODULES)
def test_same_markdown_files(slug):
    vi = sorted(p.name for p in (ROOT / "modules" / slug).glob("*.md"))
    en = sorted(p.name for p in (EN / "modules" / slug).glob("*.md"))
    assert en == vi


@pytest.mark.parametrize("slug", EN_MODULES)
def test_same_sections_questions_and_sources(slug):
    for vi_md in sorted((ROOT / "modules" / slug).glob("*.md")):
        vi, en = _read(vi_md), _read(EN / "modules" / slug / vi_md.name)
        where = f"{slug}/{vi_md.name}"
        assert HEADING.findall(_no_code(en)) == HEADING.findall(_no_code(vi)), f"{where}: khác cấu trúc mục"
        assert len(QUESTION.findall(en)) == len(QUESTION.findall(vi)), f"{where}: khác số câu hỏi"
        assert en.count("<details>") == vi.count("<details>"), f"{where}: khác số đáp án"
        assert set(URL.findall(en)) == set(URL.findall(vi)), f"{where}: khác link ngoài"
        if vi_md.name == "references.md":
            assert len(TABLE_ROW.findall(en)) == len(TABLE_ROW.findall(vi)), f"{where}: khác số dòng bảng"


@pytest.mark.parametrize("slug", EN_MODULES)
def test_same_example_files(slug):
    vi = _local_targets(ROOT / "modules" / slug / "README.md")
    en = _local_targets(EN / "modules" / slug / "README.md")
    assert en == vi


@pytest.mark.parametrize("slug", EN_MODULES)
def test_readme_has_traps_and_changes(slug):
    vi, en = _read(ROOT / "modules" / slug / "README.md"), _read(EN / "modules" / slug / "README.md")
    if "## Bẫy thường gặp" in vi:
        assert "## Common traps" in en
    if "## Điều gì đã thay đổi ở model 5.x" in vi:
        assert "## What changed with 5.x models" in en


@pytest.mark.parametrize("slug", EN_MODULES)
def test_english_copies_have_a_vietnamese_original(slug):
    for kind in ("python", "exercises"):
        for p in sorted((EN / "modules" / slug / kind).glob("*.py")):
            assert (ROOT / "modules" / slug / kind / p.name).is_file(), f"{p.relative_to(ROOT)}: không có bản gốc"


@pytest.mark.parametrize("slug", EN_MODULES)
def test_every_exercise_has_an_english_copy_with_the_same_api(slug):
    for vi in sorted((ROOT / "modules" / slug / "exercises").glob("*.py")):
        en = EN / "modules" / slug / "exercises" / vi.name
        assert en.is_file(), f"thiếu {en.relative_to(ROOT)}"
        assert _api(en) == _api(vi), f"{en.relative_to(ROOT)}: tên hàm/lớp/tham số khác bản tiếng Việt"


@pytest.mark.parametrize("script", EN_SCRIPTS, ids=lambda p: p.relative_to(EN).as_posix())
def test_english_script_runs_in_mock_mode(script):
    env = {k: v for k, v in os.environ.items() if k != "CHAM"}
    env["CLAUDE_MOCK"] = "1"
    r = subprocess.run([sys.executable, str(script)], cwd=ROOT, env=env, capture_output=True, text=True, check=False,
                       timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]
