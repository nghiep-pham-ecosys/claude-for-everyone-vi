"""Module 06: estimate the cost before and after calling Claude (uoc_tinh_chi_phi = estimate the cost).

Before the call: know the price (config/models.yaml) and max_tokens -> you have a CAP on the output cost.
After the call:  read msg.usage -> split the cost into input / output / thinking, compare with
estimate_cost_usd(msg). Every price is read from config/models.yaml. The script types in no price at all.

Run:  CLAUDE_MOCK=1 uv run python en/modules/06-cost/python/01_uoc_tinh_chi_phi.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))

from claude_vi import ClaudeVi, estimate_cost_usd, load_models  # noqa: E402

MTOK = 1_000_000


def gia(model: str) -> dict | None:
    """Price (gia) in USD per million tokens, from config/models.yaml. None if the model has no price."""
    return load_models()["models"].get(model, {}).get("price_per_mtok")


def tran_chi_phi_output(model: str, max_tokens: int) -> float:
    """The maximum output cost of ONE call: max_tokens is a hard cap on thinking + text."""
    p = gia(model)
    return max_tokens * p["output"] / MTOK if p else float("nan")


def tach_chi_phi(msg) -> dict:
    """Split the cost of a response by each part of usage.

    thinking is INSIDE output (already counted in "output"); it is split out only to show what it costs.
    token_cache: the number of cache write + cache read tokens. They have their own prices, split out in
    script 02; here they are only reported, so you know that "tong" (total = input + output) leaves them out.
    """
    p = gia(msg.model)
    u = msg.usage
    thinking = (u.output_tokens_details.thinking_tokens if u.output_tokens_details else None) or 0
    cache = (u.cache_creation_input_tokens or 0) + (u.cache_read_input_tokens or 0)
    if not p:
        nan = float("nan")
        return {"input": nan, "output": nan, "thinking": nan, "tong": nan, "token_cache": cache}
    vao = u.input_tokens * p["input"] / MTOK
    ra = u.output_tokens * p["output"] / MTOK
    return {
        "input": vao,
        "output": ra,
        "thinking": thinking * p["output"] / MTOK,
        "tong": vao + ra,
        "token_cache": cache,
    }


def main() -> None:
    client = ClaudeVi()
    model, max_tokens = client.settings.model, client.settings.max_tokens
    cfg = load_models()["models"]

    print(f"1) Price table in config/models.yaml (USD / MTok), output cap with max_tokens={max_tokens}")
    print(f"   {'model':<20}{'input':>8}{'output':>8}{'output cap':>14}")
    for m, entry in cfg.items():
        if entry.get("status") != "active":
            continue
        p = gia(m)
        cap = "$" + format(tran_chi_phi_output(m, max_tokens), ".6f")
        print(f"   {m:<20}{p['input']:>8}{p['output']:>8}{cap:>14}")

    cap = tran_chi_phi_output(model, max_tokens)
    print(f"\n2) Before calling {model}: the output costs at most ${cap:.6f}.")
    print("   The input is not known in advance: count it with client.count_tokens(...) (script 03),"
          "\n   or measure it from one identical call.")

    print("\n3) After the call: read usage, split the cost")
    question = "Explain briefly why you should measure the cost on your own task."
    for effort in ("low", "high"):
        msg = client.ask(question, output_config={"effort": effort})
        u, c = msg.usage, tach_chi_phi(msg)
        print(f"   effort={effort:<5} {u.input_tokens} in / {u.output_tokens} out"
              f" | input ${c['input']:.8f} + output ${c['output']:.8f} (thinking ${c['thinking']:.8f})"
              f" = ${c['tong']:.8f} | estimate_cost_usd ${estimate_cost_usd(msg):.8f}")
        if c["token_cache"]:
            print(f"   {c['token_cache']} cache tokens have their own price, not in 'tong' (see script 02).")

    print("\n4) Cache: usage also has cache_creation_input_tokens and cache_read_input_tokens."
          "\n   This request sets no cache_control, so both are 0. Script 02 turns on prompt caching"
          "\n   and prices the cache.")


if __name__ == "__main__":
    main()
