"""Shared parts of the module 08 scripts: the client, the lab assistant's tools, the cost log
(phong_thi_nghiem = laboratory).

All data is made up: the handbook of module 04, the two AQI/temperature tools of module 03, and one page
with an injected instruction. Running this file directly does not call Claude.
"""
from __future__ import annotations

import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "shared" / "py"))
sys.path.insert(0, str(ROOT / "en" / "modules" / "03-tool-use" / "python"))

from claude_vi import ClaudeVi, Settings, estimate_cost_usd, load_models  # noqa: E402
from claude_vi.mock import MockAnthropic  # noqa: E402
from tools_mau import GET_AQI, GET_TEMPERATURE  # noqa: E402,F401
from tools_mau import REGISTRY as ENV_TOOLS  # noqa: E402,F401

HANDBOOK = ROOT / "modules" / "04-rag" / "data" / "so_tay"
DATA = ROOT / "modules" / "08-agents-workflows" / "data"
INJECTED_PAGE = "99_ghi_chu_ca_dem"   # the page with an injected instruction (section 6); "night shift notes"


def make_client(settings: Settings | None = None) -> ClaudeVi:
    """ClaudeVi for module 08. In mock mode it turns on multi_step: each turn the mock calls ONE tool,
    like an agent that takes several steps.

    ClaudeVi() builds MockAnthropic() without multi_step by default, so an agent loop always stops after one
    tool round. On the real API, ClaudeVi(settings) uses the real SDK and multi_step does not matter.
    """
    s = settings or Settings.from_env()
    return ClaudeVi(settings=s, client=MockAnthropic(multi_step=True)) if s.mock else ClaudeVi(settings=s)


def list_pages() -> list[str]:
    return sorted(p.stem for p in HANDBOOK.glob("*.md"))


def read_page(page: str) -> str:
    """The text of one handbook page (module 04) or of the module 08 sample page. Unknown name -> FileNotFoundError.

    The pages are in Vietnamese, as in module 04.
    """
    for folder in (HANDBOOK, DATA):
        path = folder / f"{page}.md"
        if path.is_file():
            return path.read_text("utf-8")
    raise FileNotFoundError(f"no page '{page}'. Pages available: {', '.join(list_pages())}")


def read_handbook_tool(pages: list[str]) -> dict:
    """A read-only tool. The page list is an enum: Claude can only pick the pages of this task.

    The tool name stays doc_so_tay ("read handbook"), the same as in the Vietnamese edition.
    """
    return {
        "name": "doc_so_tay",
        "description": (
            "Read one page of the (fictional) lab handbook, word for word. The pages are in Vietnamese. "
            "Use it when you need a measuring procedure, a device error code, or the notes of the last shift. "
            "Read only: it changes nothing. Only accepts a page name from the enum list."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {"page": {"type": "string", "enum": pages}},
            "required": ["page"],
            "additionalProperties": False,
        },
    }


WRITE_LOG = {
    "name": "ghi_nhat_ky",   # "write to the log", the same name as in the Vietnamese edition
    "description": (
        "Write ONE line to the lab's measurement log. It has a side effect: a line once written cannot be "
        "deleted. Only use it when the user asks to write to the log. Each write needs approval from the person "
        "in charge."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {"text": {"type": "string", "description": "one line, no line breaks"}},
        "required": ["text"],
        "additionalProperties": False,
    },
}


def make_log(path: Path | None = None):
    """A ghi_nhat_ky function that writes to a temporary file (never committed). Returns (function, file path)."""
    path = path or Path(tempfile.mkdtemp(prefix="nhat_ky_")) / "nhat_ky.txt"

    def ghi_nhat_ky(text: str) -> dict:
        with path.open("a", encoding="utf-8") as f:
            f.write(text.replace("\n", " ") + "\n")
        return {"written": True, "file": path.name}

    return ghi_nhat_ky, path


def output_cap_usd(model: str, max_tokens: int) -> float:
    """The highest output cost of ONE call (module 06 section 3): max_tokens is a hard cap for thinking + text."""
    price = load_models()["models"].get(model, {}).get("price_per_mtok")
    return max_tokens * price["output"] / 1_000_000 if price else float("nan")


class CostLog:
    """Records every Message of one run, to add up the calls, tokens and cost.

    Total cost = the sum of estimate_cost_usd over EVERY call, not just the last one.
    It is still a rough estimate: it ignores cache tokens (module 06 section 5).
    """

    def __init__(self) -> None:
        self.msgs: list = []
        self._lock = threading.Lock()   # script 04 records from several threads

    def add(self, msg):
        with self._lock:
            self.msgs.append(msg)
        return msg

    @property
    def calls(self) -> int:
        return len(self.msgs)

    @property
    def usd(self) -> float:
        return sum(estimate_cost_usd(m) for m in self.msgs)

    def report(self) -> str:
        tokens_in = sum(m.usage.input_tokens for m in self.msgs)
        tokens_out = sum(m.usage.output_tokens for m in self.msgs)
        return f"{self.calls} calls, {tokens_in} input tokens, {tokens_out} output tokens, ≈ ${self.usd:.6f}"
