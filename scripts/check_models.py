#!/usr/bin/env python3
"""Quét mọi chuỗi claude-* trong repo, đối chiếu config/models.yaml.

- Model không có trong allowlist  -> lỗi
- Model retired ngoài legacy/     -> lỗi
- Model deprecated ngoài legacy/  -> cảnh báo
Thoát mã 1 nếu có lỗi.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(r"\bclaude-(?:fable|mythos|opus|sonnet|haiku|3|2|instant)[a-z0-9.\-]*\b")
SCAN_SUFFIXES = {".py", ".ts", ".ipynb", ".md", ".yml", ".yaml", ".json", ".toml"}
SKIP_DIRS = {".git", ".venv", "node_modules", "fixtures", "site", "tests"}  # tests cố ý dùng model sai
SKIP_FILES = {ROOT / "config" / "models.yaml"}
# Tên package/module chứa chữ "claude-" nhưng không phải model ID
IGNORE = {"claude-agent-sdk"}


def main() -> int:
    cfg = yaml.safe_load((ROOT / "config" / "models.yaml").read_text("utf-8"))["models"]
    errors, warnings = [], []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in SCAN_SUFFIXES or path in SKIP_FILES:
            continue
        rel = path.relative_to(ROOT)
        if SKIP_DIRS & set(rel.parts):
            continue
        in_legacy = "legacy" in rel.parts or "docs" in rel.parts
        for lineno, line in enumerate(path.read_text("utf-8", errors="ignore").splitlines(), 1):
            for m in PATTERN.finditer(line):
                model = m.group(0).rstrip(".-")
                if model in IGNORE:
                    continue
                where = f"{rel}:{lineno}"
                entry = cfg.get(model)
                if entry is None:
                    errors.append(f"{where}: '{model}' không có trong config/models.yaml")
                elif entry.get("status") == "retired" and not in_legacy:
                    errors.append(f"{where}: '{model}' đã retired")
                elif entry.get("status") == "deprecated" and not in_legacy:
                    warnings.append(f"{where}: '{model}' deprecated, retire {entry.get('retire_on')}")
    for w in warnings:
        print(f"CẢNH BÁO  {w}")
    for e in errors:
        print(f"LỖI       {e}")
    print(f"\n{len(errors)} lỗi, {len(warnings)} cảnh báo")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
