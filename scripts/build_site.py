#!/usr/bin/env python3
"""Dựng trang GitHub Pages của khoá học từ README các module.

    uv run python scripts/build_site.py --out _site

- Mỗi thư mục `modules/NN-ten/` có `README.md` thành một trang `<out>/NN-ten/index.html`.
- `docs/pages/videos.yaml` ghi video của từng module. Ô `video` để trống thì trang chỉ báo
  "video đang được sản xuất", không có khung nhúng hỏng. Chỉ nhận link YouTube.
- Link tương đối trong README: tới README module khác thì thành trang của module đó,
  còn lại (script, bài tập, references...) trỏ về file trên GitHub.
- Không cần mạng, không gọi API. Chỉ dùng thư viện chuẩn và `pyyaml`.

Bộ chuyển Markdown bên dưới chỉ phủ phần cú pháp các README đang dùng: tiêu đề, đoạn văn,
danh sách, bảng, khối code, trích dẫn, `code`, **đậm**, *nghiêng*, [link](url).
"""
from __future__ import annotations

import argparse
import html
import posixpath
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
SITE_SRC = ROOT / "docs" / "pages"
MANIFEST = SITE_SRC / "videos.yaml"

# Dòng này phải có trên mọi trang (CLAUDE.md, luật 9).
DISCLAIMER = "không chính thức, không được Anthropic bảo trợ"
FOOTER = (
    f"Dự án cộng đồng, {DISCLAIMER}. "
    "“Claude” và “Anthropic” là thương hiệu của Anthropic PBC. "
    "Code: MIT. Nội dung bài giảng: CC BY 4.0."
)

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be",
                 "youtube-nocookie.com", "www.youtube-nocookie.com"}
YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


# ---------------------------------------------------------------- video


def youtube_embed(url: str | None) -> str | None:
    """Link YouTube -> link nhúng youtube-nocookie. Rỗng -> None. Link lạ -> ValueError."""
    url = (url or "").strip()
    if not url:
        return None
    u = urlparse(url)
    if u.scheme != "https" or u.hostname not in YOUTUBE_HOSTS:
        raise ValueError(f"chỉ nhận link YouTube https: {url!r}")
    vid = ""
    if u.hostname == "youtu.be":
        vid = u.path.lstrip("/")
    elif u.path == "/watch":
        vid = (parse_qs(u.query).get("v") or [""])[0]
    elif u.path.startswith(("/embed/", "/shorts/", "/live/")):
        vid = u.path.split("/")[2]
    if not YOUTUBE_ID.match(vid):
        raise ValueError(f"không đọc được ID video trong {url!r}")
    return f"https://www.youtube-nocookie.com/embed/{vid}"


# ---------------------------------------------------------------- dữ liệu


@dataclass
class Module:
    slug: str          # "01-messages-api"
    title: str         # "01 · Messages API"
    body_md: str       # README bỏ dòng tiêu đề đầu
    level: str         # "Cơ bản" / "Trung cấp" / "Nâng cao" / ""
    embed: str | None  # link nhúng, None nếu chưa có video


def load_manifest(path: Path = MANIFEST) -> dict:
    data = yaml.safe_load(path.read_text("utf-8")) or {}
    if not isinstance(data.get("repo"), str) or "/" not in data["repo"]:
        raise ValueError(f"{path}: thiếu `repo: <owner>/<tên>`")
    mods = data.get("modules") or {}
    if not isinstance(mods, dict):
        raise TypeError(f"{path}: `modules` phải là bảng slug -> {{video: ...}}")
    return {"repo": data["repo"], "modules": mods}


def levels_from_readme(readme: str) -> dict[str, str]:
    """Đọc cột "Cấp" của bảng Lộ trình trong README gốc."""
    rx = re.compile(r"^\|\s*([^|]+?)\s*\|\s*\[[^\]]*\]\(modules/([^/)]+)/README\.md\)", re.MULTILINE)
    return {slug: level for level, slug in rx.findall(readme)}


def load_modules(root: Path, manifest: dict) -> list[Module]:
    dirs = sorted(p for p in (root / "modules").iterdir() if (p / "README.md").is_file())
    slugs = [p.name for p in dirs]
    entries = manifest["modules"]
    missing = [s for s in slugs if s not in entries]
    unknown = [s for s in entries if s not in slugs]
    if missing or unknown:
        raise ValueError(f"videos.yaml lệch thư mục modules/: thiếu {missing}, thừa {unknown}")
    levels = levels_from_readme((root / "README.md").read_text("utf-8"))
    out = []
    for p in dirs:
        text = p.joinpath("README.md").read_text("utf-8")
        first, _, rest = text.partition("\n")
        if not first.startswith("# "):
            raise ValueError(f"{p.name}/README.md: dòng đầu phải là tiêu đề `# ...`")
        entry = entries[p.name] or {}
        out.append(Module(p.name, first[2:].strip(), rest, levels.get(p.name, ""),
                          youtube_embed(entry.get("video"))))
    return out


# ---------------------------------------------------------------- link


class Linker:
    """Đổi link tương đối của một README thành link dùng được trên site."""

    def __init__(self, repo: str, root: Path, src_dir: str, to_root: str, slugs: set[str]):
        self.repo, self.root, self.src_dir = repo, root, src_dir
        self.to_root, self.slugs = to_root, slugs

    def __call__(self, url: str) -> str:
        if re.match(r"^[a-z][a-z0-9+.-]*:", url, re.IGNORECASE) or url.startswith(("#", "//")):
            return url
        path, sep, frag = url.partition("#")
        frag = sep + frag
        resolved = posixpath.normpath(posixpath.join(self.src_dir, path)) if path else self.src_dir
        if resolved.startswith(".."):
            return url
        m = re.fullmatch(r"modules/([^/]+)(?:/README\.md)?/?", resolved)
        if m and m.group(1) in self.slugs:
            return f"{self.to_root}{m.group(1)}/index.html{frag}"
        if resolved == "README.md":
            return f"{self.to_root}index.html{frag}"
        kind = "tree" if (self.root / resolved).is_dir() else "blob"
        return f"https://github.com/{self.repo}/{kind}/main/{resolved}{frag}"


# ---------------------------------------------------------------- Markdown


def slugify(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text).lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s+", "-", text.strip()) or "muc"


def inline(text: str, link) -> str:
    codes: list[str] = []

    def keep_code(m: re.Match) -> str:
        codes.append(f"<code>{html.escape(m.group(2))}</code>")
        return f"\x00{len(codes) - 1}\x00"

    s = re.sub(r"(`+)(.+?)\1", keep_code, text)
    s = html.escape(s, quote=False)

    def a(m: re.Match) -> str:
        href = link(html.unescape(m.group(2)))
        return f'<a href="{html.escape(href)}">{m.group(1)}</a>'

    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", a, s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?![\s*])(.+?)(?<![\s*])\*(?![\w*])", r"<em>\1</em>", s)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], s)


def split_row(line: str) -> list[str]:
    """Tách một dòng bảng theo `|`, bỏ qua `|` nằm trong `code` hoặc đã escape."""
    line = line.strip()
    line = line.removeprefix("|")
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    cells, cur, in_code, i = [], "", False, 0
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line) and line[i + 1] == "|":
            cur += "|"
            i += 2
            continue
        if ch == "`":
            in_code = not in_code
        if ch == "|" and not in_code:
            cells.append(cur.strip())
            cur = ""
        else:
            cur += ch
        i += 1
    cells.append(cur.strip())
    return cells


TABLE_SEP = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")
UL = re.compile(r"^[-*+]\s+(.*)")
OL = re.compile(r"^\d+[.)]\s+(.*)")


def markdown(text: str, link) -> str:
    lines = text.splitlines()
    out: list[str] = []
    para: list[str] = []
    i = 0

    def flush() -> None:
        if para:
            out.append(f"<p>{inline(' '.join(para), link)}</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        fence = re.match(r"^(```+|~~~+)\s*([\w+-]*)", stripped)
        if fence:
            flush()
            mark, lang = fence.group(1), fence.group(2)
            body = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(mark):
                body.append(lines[i])
                i += 1
            cls = f' class="language-{lang}"' if lang else ""
            out.append(f"<pre><code{cls}>{html.escape(chr(10).join(body))}</code></pre>")
            i += 1
            continue
        if not stripped:
            flush()
            i += 1
            continue
        h = re.match(r"^(#{1,6})\s+(.*?)\s*#*$", stripped)
        if h:
            flush()
            n, title = len(h.group(1)), h.group(2)
            out.append(f'<h{n} id="{slugify(title)}">{inline(title, link)}</h{n}>')
            i += 1
            continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", stripped):
            flush()
            out.append("<hr>")
            i += 1
            continue
        if stripped.startswith("|") and i + 1 < len(lines) and TABLE_SEP.match(lines[i + 1]):
            flush()
            head = split_row(stripped)
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            th = "".join(f"<th>{inline(c, link)}</th>" for c in head)
            body = "".join(
                "<tr>" + "".join(f"<td>{inline(c, link)}</td>" for c in r) + "</tr>" for r in rows
            )
            out.append(f'<div class="table"><table><thead><tr>{th}</tr></thead>'
                       f"<tbody>{body}</tbody></table></div>")
            continue
        if stripped.startswith(">"):
            flush()
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append(f"<blockquote>{markdown(chr(10).join(quote), link)}</blockquote>")
            continue
        kind = UL if UL.match(stripped) else OL if OL.match(stripped) else None
        if kind:
            flush()
            items: list[list[str]] = []
            while i < len(lines):
                cur = lines[i]
                m = kind.match(cur.strip()) if not cur[:1].isspace() else None
                if m:
                    items.append([m.group(1)])
                elif cur.strip() and cur[:1].isspace() and items:
                    items[-1].append(cur.strip())   # dòng nối của mục trước
                elif not cur.strip():
                    j = i + 1
                    while j < len(lines) and not lines[j].strip():
                        j += 1
                    if j < len(lines) and kind.match(lines[j]):
                        i = j
                        continue
                    break
                else:
                    break
                i += 1
            tag = "ul" if kind is UL else "ol"
            lis = "".join(f"<li>{inline(' '.join(it), link)}</li>" for it in items)
            out.append(f"<{tag}>{lis}</{tag}>")
            continue
        para.append(stripped)
        i += 1
    flush()
    return "\n".join(out)


# ---------------------------------------------------------------- trang


def page(title: str, to_root: str, main: str) -> str:
    t = html.escape(title)
    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t} · Claude for Everyone (vi)</title>
<meta name="description" content="Lộ trình học {DISCLAIMER}, bằng tiếng Việt, về nền tảng Claude.">
<link rel="stylesheet" href="{to_root}style.css">
</head>
<body>
<header class="site">
<a class="brand" href="{to_root}index.html">Claude for Everyone (vi)</a>
<p class="notice">Lộ trình học {DISCLAIMER}.</p>
</header>
<main>
{main}
</main>
<footer class="site"><p>{FOOTER}</p></footer>
</body>
</html>
"""


def video_block(mod: Module) -> str:
    if mod.embed is None:
        return ('<p class="video-pending">Video của module này đang được sản xuất. '
                "Trong lúc chờ, bạn đọc bài bên dưới và chạy script ở mock mode.</p>")
    title = html.escape(f"Video: {mod.title}")
    return (f'<div class="video"><iframe src="{html.escape(mod.embed)}" title="{title}" '
            'loading="lazy" referrerpolicy="strict-origin-when-cross-origin" '
            'allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
            "allowfullscreen></iframe></div>")


def module_page(mod: Module, prev: Module | None, nxt: Module | None, linker: Linker) -> str:
    nav = []
    if prev:
        nav.append(f'<a href="../{prev.slug}/index.html">← {html.escape(prev.title)}</a>')
    nav.append('<a href="../index.html">Mục lục</a>')
    if nxt:
        nav.append(f'<a href="../{nxt.slug}/index.html">{html.escape(nxt.title)} →</a>')
    nav_html = f'<nav class="pager">{" ".join(nav)}</nav>'
    main = (f"<article>\n<h1>{html.escape(mod.title)}</h1>\n{video_block(mod)}\n"
            f"{markdown(mod.body_md, linker)}\n</article>\n{nav_html}")
    return page(mod.title, "../", main)


def index_page(mods: list[Module], repo: str) -> str:
    rows = []
    for m in mods:
        video = "Có video" if m.embed else "Sắp có"
        rows.append(f'<tr><td><a href="{m.slug}/index.html">{html.escape(m.title)}</a></td>'
                    f"<td>{html.escape(m.level)}</td><td>{video}</td></tr>")
    gh = f"https://github.com/{repo}"
    start = f'Bắt đầu từ <a href="{mods[0].slug}/index.html">module đầu tiên</a>.' if mods else ""
    main = f"""<h1>Claude for Everyone (vi)</h1>
<p>Lộ trình học {DISCLAIMER}, bằng tiếng Việt, về nền tảng Claude: từ lời gọi API đầu tiên tới agent và MCP.
Mỗi module có bài đọc, script chạy được ở mock mode (không cần API key), bài tập chấm bằng test và quiz.</p>
<p>Mã nguồn, bài tập và lời giải: <a href="{html.escape(gh)}">{html.escape(gh)}</a>.
{start}</p>
<h2 id="cac-module">Các module</h2>
<div class="table"><table><thead><tr><th>Module</th><th>Cấp</th><th>Video</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>"""
    return page("Mục lục", "", main)


def build(out: Path, root: Path = ROOT, manifest_path: Path | None = None) -> list[Path]:
    manifest = load_manifest(manifest_path or root / "docs" / "pages" / "videos.yaml")
    mods = load_modules(root, manifest)
    slugs = {m.slug for m in mods}
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    written = [out / "index.html"]
    written[0].write_text(index_page(mods, manifest["repo"]), "utf-8")
    shutil.copyfile(root / "docs" / "pages" / "style.css", out / "style.css")
    for k, mod in enumerate(mods):
        linker = Linker(manifest["repo"], root, f"modules/{mod.slug}", "../", slugs)
        prev = mods[k - 1] if k else None
        nxt = mods[k + 1] if k + 1 < len(mods) else None
        target = out / mod.slug / "index.html"
        target.parent.mkdir()
        target.write_text(module_page(mod, prev, nxt, linker), "utf-8")
        written.append(target)
    return written


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "_site", help="thư mục đích (bị xoá rồi dựng lại)")
    args = ap.parse_args(argv)
    try:
        pages = build(args.out.resolve())
    except (ValueError, TypeError) as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        return 1
    print(f"Đã dựng {len(pages)} trang vào {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
