"""Module 06 — ước tính chi phí trước và sau khi gọi Claude.

Trước khi gọi: biết giá (config/models.yaml) và max_tokens -> có TRẦN chi phí output.
Sau khi gọi:  đọc msg.usage -> tách chi phí input / output / thinking, so với estimate_cost_usd(msg).
Mọi giá đọc từ config/models.yaml. Script không gõ con số giá nào.

Chạy:  CLAUDE_MOCK=1 uv run python modules/06-cost/python/01_uoc_tinh_chi_phi.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from claude_vi import ClaudeVi, estimate_cost_usd, load_models  # noqa: E402

MTOK = 1_000_000


def gia(model: str) -> dict | None:
    """Giá USD / triệu token của model, lấy từ config/models.yaml. None nếu config chưa có giá."""
    return load_models()["models"].get(model, {}).get("price_per_mtok")


def tran_chi_phi_output(model: str, max_tokens: int) -> float:
    """Chi phí output tối đa của MỘT lời gọi: max_tokens là trần cứng cho thinking + text."""
    p = gia(model)
    return max_tokens * p["output"] / MTOK if p else float("nan")


def tach_chi_phi(msg) -> dict:
    """Tách chi phí của một response theo từng phần của usage.

    thinking nằm TRONG output (đã tính ở "output"), tách riêng chỉ để thấy nó tốn bao nhiêu.
    cache_*: estimate_cost_usd chưa tính, vì config chưa có giá cache. Trả về số token để bạn biết
    ước tính đang thiếu phần nào.
    """
    p = gia(msg.model)
    u = msg.usage
    thinking = (u.output_tokens_details.thinking_tokens if u.output_tokens_details else None) or 0
    cache = (u.cache_creation_input_tokens or 0) + (u.cache_read_input_tokens or 0)
    if not p:
        nan = float("nan")
        return {"input": nan, "output": nan, "thinking": nan, "tong": nan, "token_cache_chua_tinh": cache}
    vao = u.input_tokens * p["input"] / MTOK
    ra = u.output_tokens * p["output"] / MTOK
    return {
        "input": vao,
        "output": ra,
        "thinking": thinking * p["output"] / MTOK,
        "tong": vao + ra,
        "token_cache_chua_tinh": cache,
    }


def main() -> None:
    client = ClaudeVi()
    model, max_tokens = client.settings.model, client.settings.max_tokens
    cfg = load_models()["models"]

    print(f"1) Bảng giá trong config/models.yaml (USD / MTok) và trần output với max_tokens={max_tokens}")
    print(f"   {'model':<20}{'input':>8}{'output':>8}{'trần output':>14}")
    for m, entry in cfg.items():
        if entry.get("status") != "active":
            continue
        p = gia(m)
        print(f"   {m:<20}{p['input']:>8}{p['output']:>8}{'$' + format(tran_chi_phi_output(m, max_tokens), '.6f'):>14}")

    print(f"\n2) Trước khi gọi {model}: output tốn tối đa ${tran_chi_phi_output(model, max_tokens):.6f}.")
    print("   Input chưa biết trước: cần đếm token (module 06, phần sau) hoặc đo từ một lần gọi giống hệt.")

    print("\n3) Sau khi gọi: đọc usage, tách chi phí")
    cau_hoi = "Giải thích ngắn vì sao nên đo chi phí trên chính bài toán của mình."
    for effort in ("low", "high"):
        msg = client.ask(cau_hoi, output_config={"effort": effort})
        u, c = msg.usage, tach_chi_phi(msg)
        print(f"   effort={effort:<5} {u.input_tokens} vào / {u.output_tokens} ra"
              f" | input ${c['input']:.8f} + output ${c['output']:.8f} (thinking ${c['thinking']:.8f})"
              f" = ${c['tong']:.8f} | estimate_cost_usd ${estimate_cost_usd(msg):.8f}")
        if c["token_cache_chua_tinh"]:
            print(f"   {c['token_cache_chua_tinh']} token cache CHƯA được tính: ước tính đang thấp hơn thực tế.")

    print("\n4) Cache: usage còn có cache_creation_input_tokens, cache_read_input_tokens."
          "\n   Mock chưa điền hai trường này; config chưa có giá cache nên estimate_cost_usd bỏ qua chúng.")


if __name__ == "__main__":
    main()
