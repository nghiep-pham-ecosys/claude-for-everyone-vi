"""Module 06: prompt caching: write the cache once, read it many times, and price it right.

The first part of the prompt (a long system prompt) is the same across requests -> put cache_control on the
last block of that part. Call 1 WRITES the cache (costs more than normal input), later calls READ it (much
cheaper). Prices are read from config/models.yaml.

The handbook (data/so_tay_thiet_bi.md, "equipment handbook") is fictional and written in Vietnamese; it is
shared with the Vietnamese edition. The questions are in English.

Run:  CLAUDE_MOCK=1 uv run python en/modules/06-cost/python/02_prompt_caching.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "shared" / "py"))

from claude_vi import ClaudeVi, estimate_cost_usd, load_models  # noqa: E402

MTOK = 1_000_000
SO_TAY = (ROOT / "modules" / "06-cost" / "data" / "so_tay_thiet_bi.md").read_text("utf-8")  # the handbook


def system_co_cache(ttl: str | None = None) -> list[dict]:
    """A system prompt with the cache (co cache): 2 blocks; the breakpoint is on the LAST block of the part
    that does not change (the handbook)."""
    cache_control = {"type": "ephemeral", **({"ttl": ttl} if ttl else {})}
    return [
        {"type": "text", "text": "You are the lab's assistant. Answer briefly, based only on the handbook."},
        {"type": "text", "text": SO_TAY, "cache_control": cache_control},
    ]


def tach_input(msg) -> dict:
    """The four parts of the input in usage (tach = split; ghi = write, doc = read).

    Total input = doc + ghi_5m + ghi_1h + input (Prompt caching docs).
    """
    u = msg.usage
    ghi_1h = u.cache_creation.ephemeral_1h_input_tokens if u.cache_creation else 0
    return {
        "input": u.input_tokens,                   # the part AFTER the last breakpoint, normal price
        "ghi_5m": (u.cache_creation_input_tokens or 0) - ghi_1h,
        "ghi_1h": ghi_1h,
        "doc": u.cache_read_input_tokens or 0,
    }


def chi_phi_neu_khong_cache(msg) -> float:
    """The cost if there were no cache: same tokens, but every input token at the normal input price."""
    p = load_models()["models"][msg.model]["price_per_mtok"]
    tong_input = sum(tach_input(msg).values())
    return (tong_input * p["input"] + msg.usage.output_tokens * p["output"]) / MTOK


def so_lan_doc_hoa_von(model: str, ttl: str = "5m") -> int:
    """The number of reads to break even: the fewest reads for the cache to cost less than resending the
    prefix every time (same prefix, input part only).

    No cache: (1 + n) times the input price. With the cache: 1 write + n reads.
    """
    entry = load_models()["models"][model]
    vao, cache = entry["price_per_mtok"]["input"], entry["cache_price_per_mtok"]
    n = 1
    while cache[f"write_{ttl}"] + n * cache["read"] >= (1 + n) * vao:
        n += 1
    return n


def in_dong(nhan: str, msg) -> None:
    """Print one line (in dong) with a label (nhan)."""
    t = tach_input(msg)
    print(f"   {nhan:<26} input {t['input']:>4} | write {t['ghi_5m'] + t['ghi_1h']:>4} | read {t['doc']:>4}"
          f" | ${estimate_cost_usd(msg):.7f} (no cache: ${chi_phi_neu_khong_cache(msg):.7f})")


def main() -> None:
    client = ClaudeVi()
    model = client.settings.model
    entry = load_models()["models"][model]

    print(f"1) How long is the prompt? The cache threshold of {model}: {entry['cache_min_tokens']} tokens")
    n = client.count_tokens(system=system_co_cache(),
                            messages=[{"role": "user", "content": "x"}]).input_tokens
    enough = "enough" if n >= entry["cache_min_tokens"] else "NOT enough"
    print(f"   count_tokens: {n} tokens -> {enough} to cache")

    print("\n2) Trap: a breakpoint on a block that changes every time (the current time) -> every call WRITES"
          "\n   the whole prefix and never reads")
    for time_now in ("08:00", "08:01"):
        wrong = [*system_co_cache(), {"type": "text", "text": f"It is now {time_now}.",
                                      "cache_control": {"type": "ephemeral"}}]
        # drop the breakpoint that is in the right place
        wrong[1] = {k: v for k, v in wrong[1].items() if k != "cache_control"}
        msg = client.create(system=wrong, messages=[{"role": "user", "content": "Hello"}])
        in_dong(f"time {time_now}", msg)

    print("\n3) In the right place: the breakpoint at the end of the part that does not change;"
          "\n   same handbook, three different questions")
    for i, question in enumerate(["What is the maximum temperature of the LN-1200 furnace?",
                                  "How many mg does the CP-220 balance read to?",
                                  "How often is the HV-200 calibrated?"], 1):
        msg = client.create(system=system_co_cache(), messages=[{"role": "user", "content": question}])
        in_dong(f"call {i}" + (" (cache write)" if i == 1 else " (cache read)"), msg)

    print("\n4) Changing effort from the default -> the cache may be lost (docs: the messages part may be"
          "\n   lost, on some models tools and system too; the mock treats it as losing everything)")
    msg = client.create(system=system_co_cache(),
                        messages=[{"role": "user", "content": "The LN-1200 furnace?"}],
                        output_config={"effort": "low"})
    in_dong("effort=low", msg)

    print("\n5) A prompt shorter than the threshold: not cached, and NO error")
    short = [{"type": "text", "text": "Answer briefly.", "cache_control": {"type": "ephemeral"}}]
    in_dong("short system", client.create(system=short, messages=[{"role": "user", "content": "Hello"}]))

    print("\n6) How many reads to break even (prices in config/models.yaml)")
    print(f"   {'model':<20}{'write 5m':>9}{'write 1h':>9}{'read':>7}{'even 5m':>11}{'even 1h':>11}")
    for m, e in load_models()["models"].items():
        if e.get("status") == "active" and e.get("cache_price_per_mtok"):
            c = e["cache_price_per_mtok"]
            print(f"   {m:<20}{c['write_5m']:>9}{c['write_1h']:>9}{c['read']:>7}"
                  f"{so_lan_doc_hoa_von(m, '5m'):>5} read(s){so_lan_doc_hoa_von(m, '1h'):>5} read(s)")
    print("   Token counts come from the mock (1 token ≈ 4 characters), not real ones. Prices are the real"
          "\n   prices in the config.")


if __name__ == "__main__":
    main()
