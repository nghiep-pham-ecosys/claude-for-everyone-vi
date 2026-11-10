#!/usr/bin/env python3
"""Chạy mọi script bài học và capstone với API THẬT — dùng khi vừa cắm key.

    uv run python scripts/chay_that.py                       # chỉ liệt kê, KHÔNG gọi API
    uv run python scripts/chay_that.py --dong-y              # chạy thật tất cả
    uv run python scripts/chay_that.py --dong-y --chi 01-    # chỉ script có "01-" trong đường dẫn
    uv run python scripts/chay_that.py --dong-y --gia-dinh   # kiểm thêm 2 giả định về Haiku 5.5 (HANDOFF "Còn treo")
    uv run python scripts/chay_that.py --dong-y --ghi        # ghi response làm fixture (CLAUDE_RECORD=1)

Không có --dong-y thì script không gửi request nào. Chi phí ước tính của từng module nằm ở
references.md của module đó; với Haiku 5.5 và MAX_TOKENS=1024, cả repo hiện dưới $0,05.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared" / "py"))


def danh_sach(chi: str | None) -> list[Path]:
    """Cùng tập file mà job `test` trong ci.yml chạy ở mock mode."""
    files = sorted(ROOT.glob("modules/*/python/*.py")) + sorted(ROOT.glob("capstones/*/pipeline.py"))
    return [f for f in files if not chi or chi in str(f.relative_to(ROOT))]


def kiem_dieu_kien() -> str | None:
    """Lý do không được chạy thật, hoặc None nếu đủ điều kiện."""
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env", override=False)
    if os.getenv("CLAUDE_MOCK") == "1":
        return "CLAUDE_MOCK=1 đang bật (trong shell hoặc .env). Bỏ đi để chạy thật."
    if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")):
        return "Chưa có ANTHROPIC_API_KEY. cp .env.example .env rồi điền key."
    return None


def kiem_gia_dinh() -> bool:
    """Hai request nhỏ trên Haiku 5.5 để xác nhận luật trong config/models.yaml.

    1. thinking {"type": "disabled"} ở effort high được nhận   -> rules.thinking_disabled_allowed
    2. tool_choice any được nhận và response bỏ thinking         -> rules.forced_tool_choice_allowed
    """
    import anthropic
    from claude_vi import ClaudeVi, Settings

    client = ClaudeVi(Settings(model="claude-haiku-5-5", max_tokens=128, mock=False, record=False))
    ok = True

    try:
        msg = client.ask("Trả lời đúng một từ: xin chào", thinking={"type": "disabled"},
                         output_config={"effort": "high"})
        co_thinking = any(b.type == "thinking" for b in msg.content)
        print(f"[1] thinking disabled: ĐƯỢC NHẬN (stop_reason={msg.stop_reason}, "
              f"{'vẫn có' if co_thinking else 'không có'} block thinking)")
    except anthropic.BadRequestError as e:
        ok = False
        print(f"[1] thinking disabled: 400 -> sửa thinking_disabled_allowed thành false. {e.message}")

    tool = {"name": "chao", "description": "Chào người dùng bằng tên.",
            "input_schema": {"type": "object", "properties": {"ten": {"type": "string"}},
                             "required": ["ten"], "additionalProperties": False}}
    try:
        msg = client.ask("Chào Nghiệp", tools=[tool], tool_choice={"type": "any"})
        loai = [b.type for b in msg.content]
        print(f"[2] tool_choice any: ĐƯỢC NHẬN (stop_reason={msg.stop_reason}, blocks={loai})")
        if "thinking" in loai:
            ok = False
            print("    Response vẫn có thinking — khác docs; xem lại mock trong claude_vi/mock.py.")
    except anthropic.BadRequestError as e:
        ok = False
        print(f"[2] tool_choice any: 400 -> sửa forced_tool_choice_allowed thành false. {e.message}")
    return ok


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dong-y", action="store_true", help="đồng ý gọi API thật (tốn tiền)")
    ap.add_argument("--chi", help="chỉ chạy file có chuỗi này trong đường dẫn")
    ap.add_argument("--ghi", action="store_true", help="ghi response làm fixture (CLAUDE_RECORD=1)")
    ap.add_argument("--gia-dinh", action="store_true", help="kiểm 2 giả định về Haiku 5.5 trước")
    args = ap.parse_args(argv)

    files = danh_sach(args.chi)
    print(f"{len(files)} script sẽ chạy với API thật:")
    for f in files:
        print("  ", f.relative_to(ROOT))
    if not args.dong_y:
        print("\nChưa gửi request nào. Thêm --dong-y để chạy thật.")
        return 0
    ly_do = kiem_dieu_kien()
    if ly_do:
        print(f"\nKhông chạy: {ly_do}")
        return 2

    ok_gia_dinh = True
    if args.gia_dinh:
        print("\n== Kiểm giả định Haiku 5.5 ==")
        ok_gia_dinh = kiem_gia_dinh()

    env = {**os.environ, "CLAUDE_MOCK": "0", "CLAUDE_RECORD": "1" if args.ghi else "0"}
    loi = []
    for f in files:
        rel = f.relative_to(ROOT)
        print(f"\n== {rel} ==", flush=True)
        t0 = time.monotonic()
        try:
            rc = subprocess.run([sys.executable, str(f)], check=False, env=env, cwd=ROOT, timeout=600).returncode
        except subprocess.TimeoutExpired:
            rc = "timeout"
        print(f"-- {rel}: {'OK' if rc == 0 else f'LỖI ({rc})'} sau {time.monotonic() - t0:.1f}s")
        if rc != 0:
            loi.append(str(rel))

    print(f"\n{len(files) - len(loi)}/{len(files)} script chạy được với API thật.")
    for r in loi:
        print("  LỖI", r)
    if args.ghi:
        print("Fixture mới ở shared/py/claude_vi/fixtures/ — xem lại trước khi commit.")
    return 1 if loi or not ok_gia_dinh else 0


if __name__ == "__main__":
    sys.exit(main())
