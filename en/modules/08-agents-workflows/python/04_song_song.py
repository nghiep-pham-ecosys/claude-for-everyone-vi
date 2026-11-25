"""Module 08: running in parallel: sectioning and voting (song_song = parallel).

Sectioning: one call per handbook page, run at the same time, then the code merges the results.
Voting: the same question asked several times, and the majority wins.

Three things to always do:
  - cap the number of calls at the same time (max_workers), so you do not cause 429 errors yourself;
  - catch TYPED errors in each branch: one broken branch does not crash the whole run;
  - do not wrap another retry loop around the call: the SDK already retries 429 and 5xx (module 01 section 7).
One ClaudeVi per branch: the simplest way, and it does not depend on whether a client can be shared
between threads.

Run:  CLAUDE_MOCK=1 uv run python en/modules/08-agents-workflows/python/04_song_song.py
"""
import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import anthropic  # noqa: E402
from phong_thi_nghiem import CostLog, make_client, read_page  # noqa: E402

from claude_vi import text_of  # noqa: E402

log = CostLog()


def summarize_page(page: str) -> str:
    """One branch. An error comes back as a string with its type; it is not raised."""
    try:
        content = read_page(page)
        msg = log.add(make_client().ask(f"<page>\n{content}\n</page>\n\nSummarize this page in one sentence."))
        return text_of(msg)
    except (anthropic.APIError, OSError) as e:
        return f"ERROR {type(e).__name__}: {e}"


pages = ["01_hieu_chuan_ph", "03_lay_mau_nuoc", "05_do_do_quang", "08_khong_co"]   # the last page does not exist
with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(summarize_page, pages))   # map keeps the order of the pages
print("Sectioning:")
for p, r in zip(pages, results):
    print(f"  {p}: {r[:80]}")
errors = sum(r.startswith("ERROR") for r in results)
print(f"  Merged: {len(pages) - errors}/{len(pages)} branches succeeded; "
      "the failed branch is reported and does not crash the run.")

SCHEMA = {"type": "object",
          "properties": {"conclusion": {"type": "string", "enum": ["measure_again", "not_needed"]}},
          "required": ["conclusion"], "additionalProperties": False}
question = (read_page("02_ma_loi_md300")
            + "\n\nWhen the meter shows E-31, does the sample need to be measured again?")


def one_vote(_: int) -> str | None:
    try:
        msg = log.add(make_client().ask(question,
                                        output_config={"format": {"type": "json_schema", "schema": SCHEMA}}))
        return json.loads(text_of(msg))["conclusion"] if msg.stop_reason == "end_turn" else None
    except anthropic.APIError:
        return None


with ThreadPoolExecutor(max_workers=3) as pool:
    votes = [v for v in pool.map(one_vote, range(3)) if v]
if not votes:
    raise SystemExit("No valid vote: no conclusion.")
label, count = Counter(votes).most_common(1)[0]
print(f"\nVoting: {votes} -> {label} ({count}/{len(votes)})")
print("The mock always returns the same label for the same question; with the real API the votes can differ.")
print("\nWhole run:", log.report())
