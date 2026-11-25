"""Test cho scripts/build_site.py: dựng site vào thư mục tạm, không gọi mạng."""
from __future__ import annotations

import re
from pathlib import Path

import build_site as bs
import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULES = sorted(p.name for p in (ROOT / "modules").iterdir() if (p / "README.md").is_file())


@pytest.fixture(scope="module")
def site(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("site") / "_site"
    bs.build(out)
    return out


def _pages(site: Path) -> list[Path]:
    return sorted(site.rglob("*.html"))


def test_index_lists_every_module(site):
    index = (site / "index.html").read_text("utf-8")
    for slug in MODULES:
        assert f'href="{slug}/index.html"' in index
        assert (site / slug / "index.html").is_file()


def test_every_page_keeps_disclaimer_and_vietnamese(site):
    pages = _pages(site)
    assert len(pages) == len(MODULES) + 1
    for p in pages:
        text = p.read_text("utf-8")
        assert "không chính thức, không được Anthropic bảo trợ" in text, p
        assert '<html lang="vi">' in text
        assert "<img" not in text, "không dùng logo hay ảnh"


def test_no_embed_while_video_is_empty(site):
    manifest = bs.load_manifest()
    for slug in MODULES:
        text = (site / slug / "index.html").read_text("utf-8")
        if manifest["modules"][slug].get("video"):
            assert "<iframe" in text
        else:
            assert "<iframe" not in text
            assert 'class="video-pending"' in text


def test_published_video_is_embedded(tmp_path):
    manifest = tmp_path / "videos.yaml"
    entries = "".join(f"  {s}:\n    video: \"\"\n" for s in MODULES[1:])
    manifest.write_text(
        "repo: example/khoa-hoc\nmodules:\n"
        f"  {MODULES[0]}:\n    video: https://youtu.be/AbCdEfGhIjK\n" + entries, "utf-8")
    out = tmp_path / "_site"
    bs.build(out, manifest_path=manifest)
    first = (out / MODULES[0] / "index.html").read_text("utf-8")
    assert 'src="https://www.youtube-nocookie.com/embed/AbCdEfGhIjK"' in first
    assert "<iframe" not in (out / MODULES[1] / "index.html").read_text("utf-8")
    assert "Có video" in (out / "index.html").read_text("utf-8")


def test_manifest_matches_module_folders():
    assert sorted(bs.load_manifest()["modules"]) == MODULES


def test_manifest_drift_fails(tmp_path):
    manifest = tmp_path / "videos.yaml"
    manifest.write_text(f"repo: example/khoa-hoc\nmodules:\n  {MODULES[0]}:\n    video: \"\"\n", "utf-8")
    with pytest.raises(ValueError, match="lệch"):
        bs.build(tmp_path / "_site", manifest_path=manifest)


@pytest.mark.parametrize("url, vid", [
    ("https://www.youtube.com/watch?v=AbCdEfGhIjK", "AbCdEfGhIjK"),
    ("https://youtube.com/watch?v=AbCdEfGhIjK&t=30s", "AbCdEfGhIjK"),
    ("https://youtu.be/AbCdEfGhIjK", "AbCdEfGhIjK"),
    ("https://www.youtube.com/embed/AbCdEfGhIjK", "AbCdEfGhIjK"),
])
def test_youtube_embed_accepts_youtube_links(url, vid):
    assert bs.youtube_embed(url) == f"https://www.youtube-nocookie.com/embed/{vid}"


@pytest.mark.parametrize("url", ["", "  ", None])
def test_youtube_embed_empty_means_no_video(url):
    assert bs.youtube_embed(url) is None


@pytest.mark.parametrize("url", [
    "http://www.youtube.com/watch?v=AbCdEfGhIjK",       # không https
    "https://example.com/watch?v=AbCdEfGhIjK",          # không phải YouTube
    "https://www.youtube.com/watch?v=ngan",             # ID sai
    "https://www.youtube.com/playlist?list=PL123",      # không phải một video
    'https://youtu.be/AbCdEfGhIjK"><script>',           # chèn HTML
])
def test_youtube_embed_rejects_other_links(url):
    with pytest.raises(ValueError):
        bs.youtube_embed(url)


def test_relative_links_point_to_existing_targets(site):
    repo = re.escape(bs.load_manifest()["repo"])
    gh = re.compile(rf'href="https://github\.com/{repo}/(?:blob|tree)/main/([^"#]+)')
    local = re.compile(r'href="(?!https?:|#|mailto:)([^"#]+)')
    for p in _pages(site):
        text = p.read_text("utf-8")
        for rel in gh.findall(text):
            assert (ROOT / rel).exists(), f"{p.relative_to(site)}: {rel}"
        for rel in local.findall(text):
            assert (p.parent / rel).resolve().exists(), f"{p.relative_to(site)}: {rel}"


def test_markdown_subset():
    link = bs.Linker("example/khoa-hoc", ROOT, "modules/01-messages-api", "../", {"01-messages-api"})
    md = (
        "## Tiêu đề\n\nĐoạn có `a | b`, **đậm**, *nghiêng* và [bài](python/01_hello.py).\n\n"
        "| Cột | Ghi chú |\n|---|---|\n| `x | y` | [module](../01-messages-api/README.md#muc) |\n\n"
        "- một\n- hai <script>\n\n1. ba\n\n> trích dẫn\n\n```python\nprint('<b>')\n```\n"
    )
    out = bs.markdown(md, link)
    assert '<h2 id="tiêu-đề">Tiêu đề</h2>' in out
    assert "<code>a | b</code>" in out and "<strong>đậm</strong>" in out and "<em>nghiêng</em>" in out
    assert 'href="https://github.com/example/khoa-hoc/blob/main/modules/01-messages-api/python/01_hello.py"' in out
    assert "<td><code>x | y</code></td>" in out
    assert 'href="../01-messages-api/index.html#muc"' in out
    assert "<li>hai &lt;script&gt;</li>" in out and "<ol><li>ba</li></ol>" in out
    assert "<blockquote><p>trích dẫn</p></blockquote>" in out
    assert "print(&#x27;&lt;b&gt;&#x27;)" in out


def test_cli_builds_into_out(tmp_path, capsys):
    assert bs.main(["--out", str(tmp_path / "_site")]) == 0
    assert (tmp_path / "_site" / "style.css").is_file()
