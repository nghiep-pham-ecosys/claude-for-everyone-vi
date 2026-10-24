#!/usr/bin/env python3
"""Đối chiếu config/models.yaml với Models API (GET /v1/models).

    uv run python scripts/model_sync.py            # cần ANTHROPIC_API_KEY; chỉ in báo cáo
    uv run python scripts/model_sync.py --write    # sửa YAML, giữ nguyên comment
    uv run python scripts/model_sync.py --issue    # lệch thì mở issue qua gh
    uv run python scripts/model_sync.py --fixture tests/fixtures/models_list.json   # không gọi mạng

Phát hiện:
- model mới trên API chưa có trong YAML (không tính model đã retired)
- model có trong YAML nhưng API không còn trả về
- rules.thinking_disabled_allowed lệch capabilities.thinking.types.disabled.supported
- status lệch lifecycle
- max_tokens, server_tools khác API (chỉ là thông tin, --write tự điền)

--write KHÔNG thêm hay xoá model: model mới cần link release note và giá (CLAUDE.md, luật 2),
nên chỉ được báo cáo để người thêm tay.
Thoát mã 1 nếu còn lệch cần người xử lý.
"""
from __future__ import annotations

import argparse
import itertools
import json
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from anthropic.types import ModelInfo

ROOT = Path(__file__).resolve().parents[1]
MODELS_FILE = ROOT / "config" / "models.yaml"
LIFECYCLES = ["active", "deprecated", "retired"]  # mặc định API bỏ retired; xin cả ba

# Một trang của GET /v1/models: (data, has_more, last_id)
Page = tuple[list[ModelInfo], bool, "str | None"]
PageFetcher = Callable[["str | None"], Page]


def fetch_all(fetch_page: PageFetcher) -> list[ModelInfo]:
    """Đi hết các trang theo con trỏ after_id = last_id của trang trước."""
    models: list[ModelInfo] = []
    after_id = None
    while True:
        data, has_more, last_id = fetch_page(after_id)
        models.extend(data)
        if not has_more or not last_id:
            return models
        if last_id == after_id:
            raise RuntimeError(f"Phân trang không tiến: last_id={last_id} lặp lại")
        after_id = last_id


def api_fetcher() -> PageFetcher:
    from anthropic import Anthropic
    from dotenv import load_dotenv

    load_dotenv()
    client = Anthropic()

    def fetch(after_id: str | None) -> Page:
        kw = {"after_id": after_id} if after_id else {}
        page = client.models.list(limit=100, lifecycle=LIFECYCLES, **kw)
        return list(page.data), bool(page.has_more), page.last_id

    return fetch


def fixture_fetcher(path: Path) -> PageFetcher:
    """Đọc file JSON là mảng các response /v1/models theo thứ tự trang.

    Mỗi model được validate bằng anthropic.types.ModelInfo: fixture sai shape thì test đỏ.
    """
    pages = json.loads(path.read_text("utf-8"))

    def fetch(after_id: str | None) -> Page:
        if after_id is None:
            raw = pages[0]
        else:
            raw = next(p for prev, p in itertools.pairwise(pages) if prev["last_id"] == after_id)
        return [ModelInfo.model_validate(m) for m in raw["data"]], raw["has_more"], raw["last_id"]

    return fetch


@dataclass(frozen=True)
class Remote:
    id: str
    lifecycle: str
    thinking_disabled: bool | None
    server_tools: list[str]
    max_tokens: int | None


def summarize(m: ModelInfo) -> Remote:
    caps = m.capabilities
    tools: list[str] = []
    if caps and caps.server_tools.supported:
        # Lấy mọi tool có supported=true, kể cả tool SDK mới thêm sau này
        tools = sorted(
            k for k, v in caps.server_tools.model_dump().items() if isinstance(v, dict) and v.get("supported")
        )
    return Remote(
        id=m.id,
        lifecycle=m.lifecycle,
        thinking_disabled=caps.thinking.types.disabled.supported if caps else None,
        server_tools=tools,
        max_tokens=m.max_tokens,
    )


@dataclass
class Report:
    new: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    thinking: list[tuple[str, Any, bool]] = field(default_factory=list)  # (id, local, api)
    lifecycle: list[tuple[str, Any, str]] = field(default_factory=list)
    info: list[tuple[str, str, Any, Any]] = field(default_factory=list)  # (id, field, local, api)

    @property
    def drift(self) -> bool:
        return bool(self.new or self.missing or self.thinking or self.lifecycle)

    def unresolved(self, written: bool) -> bool:
        """Lệch còn cần người xử lý sau khi (có thể) đã --write."""
        return bool(self.new or self.missing) or (not written and self.drift)


def compare(local: dict[str, Any], remote: list[Remote]) -> Report:
    loc = local["models"]
    rem = {r.id: r for r in remote}
    rep = Report(
        new=sorted(i for i, r in rem.items() if i not in loc and r.lifecycle != "retired"),
        missing=sorted(i for i in loc if i not in rem),
    )
    for mid, entry in loc.items():
        r = rem.get(mid)
        if r is None:
            continue
        if entry.get("status") != r.lifecycle:
            rep.lifecycle.append((mid, entry.get("status"), r.lifecycle))
        rules = entry.get("rules") or {}
        local_td = rules.get("thinking_disabled_allowed")
        if local_td is not None and r.thinking_disabled is not None and local_td != r.thinking_disabled:
            rep.thinking.append((mid, local_td, r.thinking_disabled))
        if r.lifecycle == "retired":
            continue
        if entry.get("max_tokens") != r.max_tokens:
            rep.info.append((mid, "max_tokens", entry.get("max_tokens"), r.max_tokens))
        if list(entry.get("server_tools") or []) != r.server_tools:
            rep.info.append((mid, "server_tools", entry.get("server_tools"), r.server_tools))
    return rep


def render(rep: Report) -> str:
    """Báo cáo Markdown — in ra màn hình và dùng làm body issue."""
    lines = [f"# model-sync {date.today().isoformat()}", ""]
    if not rep.drift and not rep.info:
        return "\n".join(lines + ["config/models.yaml khớp Models API."])
    if rep.new:
        lines += ["## Model mới trên API (thêm tay kèm link release note và giá)", ""]
        lines += [f"- `{m}`" for m in rep.new] + [""]
    if rep.missing:
        lines += ["## Có trong YAML nhưng API không trả về", ""]
        lines += [f"- `{m}`" for m in rep.missing] + [""]
    if rep.thinking:
        lines += ["## thinking_disabled_allowed lệch `thinking.types.disabled.supported`", "",
                  "| Model | YAML | API |", "|---|---|---|"]
        lines += [f"| `{m}` | {a} | {b} |" for m, a, b in rep.thinking] + [""]
    if rep.lifecycle:
        lines += ["## status lệch lifecycle", "", "| Model | YAML | API |", "|---|---|---|"]
        lines += [f"| `{m}` | {a} | {b} |" for m, a, b in rep.lifecycle] + [""]
    if rep.info:
        lines += ["## Thông tin khác API (--write tự điền)", "", "| Model | Trường | YAML | API |",
                  "|---|---|---|---|"]
        lines += [f"| `{m}` | {f} | {a} | {b} |" for m, f, a, b in rep.info] + [""]
    return "\n".join(lines).rstrip() + "\n"


def apply(rep: Report, path: Path) -> None:
    """Ghi các trường sửa được vào YAML. ruamel.yaml giữ comment và thứ tự key."""
    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedSeq

    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    doc = y.load(path.read_text("utf-8"))
    models = doc["models"]
    today = date.today().isoformat()

    for mid, _, api in rep.thinking:
        rules = models[mid]["rules"]
        rules["thinking_disabled_allowed"] = api
        # comment cũ (vd "chưa xác minh") không còn đúng nữa
        rules.yaml_add_eol_comment(f"# model-sync {today}: Models API", "thinking_disabled_allowed")
    for mid, _, api in rep.lifecycle:
        models[mid]["status"] = api
    inserted: dict[str, int] = {}
    for mid, name, _, api in rep.info:
        entry = models[mid]
        if name == "server_tools":
            api = CommentedSeq(api)
            api.fa.set_flow_style()
        if name in entry:
            entry[name] = api
        else:
            # chèn ngay sau status: chèn cuối entry sẽ kéo dòng trống/comment của model kế tiếp lên
            pos = (1 if "status" in entry else 0) + inserted.get(mid, 0)
            entry.insert(pos, name, api)
            inserted[mid] = inserted.get(mid, 0) + 1

    with path.open("w", encoding="utf-8") as f:
        y.dump(doc, f)


def open_issue(body: str, run: Callable[..., Any] = subprocess.run) -> Any:
    title = f"model-sync: config/models.yaml lệch Models API ({date.today().isoformat()})"
    return run(["gh", "issue", "create", "--title", title, "--body", body], check=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fixture", type=Path, help="đọc response giả lập thay vì gọi API")
    ap.add_argument("--models-file", type=Path, default=MODELS_FILE)
    ap.add_argument("--write", action="store_true", help="cập nhật YAML")
    ap.add_argument("--issue", action="store_true", help="mở issue GitHub nếu còn lệch")
    args = ap.parse_args(argv)

    from ruamel.yaml import YAML

    local = YAML(typ="safe").load(args.models_file.read_text("utf-8"))
    fetch = fixture_fetcher(args.fixture) if args.fixture else api_fetcher()
    rep = compare(local, [summarize(m) for m in fetch_all(fetch)])
    text = render(rep)
    print(text)

    if args.write and (rep.drift or rep.info):
        apply(rep, args.models_file)
        print(f"Đã cập nhật {args.models_file}")
    unresolved = rep.unresolved(written=args.write)
    if args.issue and unresolved:
        open_issue(text)
    return 1 if unresolved else 0


if __name__ == "__main__":
    sys.exit(main())
