"""Module 06: count tokens BEFORE the call with count_tokens, then block requests over budget.

(dem_token = count tokens.) count_tokens takes almost the same parameters as create (system, tools, messages,
thinking...) but NOT max_tokens. It creates no message, uses no cache, and is free (it has its own
requests-per-minute limit).

Run:  CLAUDE_MOCK=1 uv run python en/modules/06-cost/python/03_dem_token.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "shared" / "py"))

from claude_vi import ClaudeVi, estimate_cost_usd, load_models  # noqa: E402

MTOK = 1_000_000
SO_TAY = (ROOT / "modules" / "06-cost" / "data" / "so_tay_thiet_bi.md").read_text("utf-8")  # the handbook
NGAN_SACH_USD = 0.001  # the budget (ngan sach) for ONE request in this example

CHECK_BOOKINGS = {
    "name": "check_equipment_bookings",
    "description": "Look up the bookings of one piece of lab equipment on a given date.",
    "input_schema": {
        "type": "object",
        "properties": {"equipment_code": {"type": "string"}, "date": {"type": "string", "format": "date"}},
        "required": ["equipment_code", "date"],
        "additionalProperties": False,
    },
}


def uoc_tinh_truoc(client: ClaudeVi, params: dict) -> dict:
    """Estimate before (uoc tinh truoc): count the input with the API, add the output cap (max_tokens).

    No cache counted: the worst case.
    """
    params = dict(params)
    max_tokens = params.pop("max_tokens", client.settings.max_tokens)
    model = params.setdefault("model", client.settings.model)
    gia = load_models()["models"][model]["price_per_mtok"]
    n = client.count_tokens(**params).input_tokens
    return {
        "input_tokens": n,
        "input_usd": n * gia["input"] / MTOK,
        "tran_output_usd": max_tokens * gia["output"] / MTOK,          # the output cap
        "toi_da_usd": (n * gia["input"] + max_tokens * gia["output"]) / MTOK,   # the maximum
    }


def main() -> None:
    client = ClaudeVi()
    ask = [{"role": "user", "content": "What is the maximum temperature of the LN-1200 furnace, in degrees?"}]

    print("1) The same question with more and more context: the input grows with system and tool definitions")
    variants = {
        "question only": {"messages": ask},
        "+ handbook system": {"system": SO_TAY, "messages": ask},
        "+ system + 1 tool": {"system": SO_TAY, "tools": [CHECK_BOOKINGS], "messages": ask},
    }
    for name, params in variants.items():
        print(f"   {name:<20} {client.count_tokens(**params).input_tokens:>5} tokens")

    print(f"\n2) Block before the call: the cap for each request is ${NGAN_SACH_USD}")
    for max_tokens in (1024, 4096):
        params = {"system": SO_TAY, "messages": ask, "max_tokens": max_tokens}
        u = uoc_tinh_truoc(client, params)
        send = u["toi_da_usd"] <= NGAN_SACH_USD
        print(f"   max_tokens={max_tokens:<5} input ${u['input_usd']:.6f}"
              f" + output cap ${u['tran_output_usd']:.6f}"
              f" = at most ${u['toi_da_usd']:.6f} -> {'SEND' if send else 'do NOT send'}")
        if send:
            msg = client.create(**params)
            print(f"   sent, real cost ${estimate_cost_usd(msg):.6f} (under the cap)")

    print("\n3) After the call: compare the count with usage"
          " (total input = input + cache write + cache read)")
    params = {"system": SO_TAY, "messages": ask}
    counted = client.count_tokens(**params).input_tokens
    msg = client.create(**params)
    u = msg.usage
    real = u.input_tokens + (u.cache_creation_input_tokens or 0) + (u.cache_read_input_tokens or 0)
    print(f"   count_tokens {counted} | usage {real} | cost ${estimate_cost_usd(msg):.6f}")
    print("   Real API: the count is an estimate and can differ a little; tokens added by the system"
          "\n   may be counted but not billed. The mock counts by the rule 1 token ≈ 4 characters,"
          "\n   so the two match.")

    print("\n4) Each model has its own tokenizer: count again with the exact model you will use")
    for m, e in load_models()["models"].items():
        if e.get("status") == "active":
            print(f"   {m:<20} {client.count_tokens(model=m, **params).input_tokens:>5} tokens")
    print("   The mock uses one way of counting for all. Docs: from model 4.7 on, the same text gives"
          "\n   about 30% more tokens than on older models, so an old count cannot be reused.")


if __name__ == "__main__":
    main()
