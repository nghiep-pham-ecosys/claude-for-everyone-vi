#!/usr/bin/env python3
"""Phát hiện pattern đã hỏng trên model 5.x trong code bài học.

Chạy trên .py, .ts, .ipynb ngoài thư mục legacy/ và docs/.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# shared/ là nơi cài luật nên cố ý nhắc tới pattern cũ
SKIP_DIRS = {".git", ".venv", "node_modules", "legacy", "docs", "scripts", "tests", "shared"}

CHECKS = [
    (re.compile(r"\b(temperature|top_p|top_k)\s*[=:]"),
     "sampling params trả 400 trên model 5.x và đã bị bỏ khỏi Python SDK ≥1.0"),
    (re.compile(r"budget_tokens"),
     "extended thinking thủ công đã bị bỏ; dùng adaptive thinking + effort"),
    (re.compile(r"""["']type["']\s*:\s*["'](any|tool)["']"""),
     "tool_choice any/tool trả 400 trên Fable 5.1, Opus 5.5, Sonnet 5.5"),
    (re.compile(r"\.content\[0\]\.text"),
     "block đầu có thể là thinking; dùng text_of(msg)"),
    (re.compile(r"""role["']?\s*[:=]\s*["']assistant["'][^}]*\}\s*\]\s*[,)]"""),
     "nghi ngờ prefill assistant ở cuối messages"),
]


def main() -> int:
    hits = 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in {".py", ".ts", ".ipynb"}:
            continue
        rel = path.relative_to(ROOT)
        if SKIP_DIRS & set(rel.parts):
            continue
        for lineno, line in enumerate(path.read_text("utf-8", errors="ignore").splitlines(), 1):
            for rx, why in CHECKS:
                if rx.search(line):
                    hits += 1
                    print(f"{rel}:{lineno}: {why}\n    {line.strip()}")
    print(f"\n{hits} vị trí cần sửa (chuyển vào legacy/ nếu cố ý giữ)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
