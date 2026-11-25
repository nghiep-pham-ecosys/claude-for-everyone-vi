"""Module 06 — prompt caching: ghi cache một lần, đọc lại nhiều lần, và tính đúng giá.

Phần đầu prompt (system dài) giống nhau giữa các request -> đánh dấu cache_control ở block cuối của phần đó.
Lần 1 GHI cache (đắt hơn input thường), các lần sau ĐỌC cache (rẻ hơn nhiều). Giá đọc từ config/models.yaml.

Chạy:  CLAUDE_MOCK=1 uv run python modules/06-cost/python/02_prompt_caching.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from claude_vi import ClaudeVi, estimate_cost_usd, load_models  # noqa: E402

MTOK = 1_000_000
SO_TAY = (Path(__file__).resolve().parents[1] / "data" / "so_tay_thiet_bi.md").read_text("utf-8")


def system_co_cache(ttl: str | None = None) -> list[dict]:
    """System gồm 2 block; breakpoint đặt ở block CUỐI của phần không đổi (sổ tay)."""
    cache_control = {"type": "ephemeral", **({"ttl": ttl} if ttl else {})}
    return [
        {"type": "text", "text": "Bạn là trợ lý của phòng thí nghiệm. Trả lời ngắn, chỉ dựa vào sổ tay."},
        {"type": "text", "text": SO_TAY, "cache_control": cache_control},
    ]


def tach_input(msg) -> dict:
    """Bốn phần của input trong usage. Tổng input = doc + ghi_5m + ghi_1h + input (docs Prompt caching)."""
    u = msg.usage
    ghi_1h = u.cache_creation.ephemeral_1h_input_tokens if u.cache_creation else 0
    return {
        "input": u.input_tokens,                                    # phần SAU breakpoint cuối, giá input thường
        "ghi_5m": (u.cache_creation_input_tokens or 0) - ghi_1h,
        "ghi_1h": ghi_1h,
        "doc": u.cache_read_input_tokens or 0,
    }


def chi_phi_neu_khong_cache(msg) -> float:
    """Cùng số token nhưng mọi token input tính giá input thường: để so cache có lợi bao nhiêu."""
    p = load_models()["models"][msg.model]["price_per_mtok"]
    tong_input = sum(tach_input(msg).values())
    return (tong_input * p["input"] + msg.usage.output_tokens * p["output"]) / MTOK


def so_lan_doc_hoa_von(model: str, ttl: str = "5m") -> int:
    """Số lần đọc ít nhất để cache rẻ hơn gửi lại prefix mỗi lần (cùng một prefix, chỉ tính phần input).

    Không cache: (1 + n) lần x giá input. Có cache: 1 lần ghi + n lần đọc.
    """
    entry = load_models()["models"][model]
    vao, cache = entry["price_per_mtok"]["input"], entry["cache_price_per_mtok"]
    n = 1
    while cache[f"write_{ttl}"] + n * cache["read"] >= (1 + n) * vao:
        n += 1
    return n


def in_dong(nhan: str, msg) -> None:
    t = tach_input(msg)
    print(f"   {nhan:<26} input {t['input']:>4} | ghi {t['ghi_5m'] + t['ghi_1h']:>4} | đọc {t['doc']:>4}"
          f" | ${estimate_cost_usd(msg):.7f} (không cache: ${chi_phi_neu_khong_cache(msg):.7f})")


def main() -> None:
    client = ClaudeVi()
    model = client.settings.model
    entry = load_models()["models"][model]

    print(f"1) Prompt dài bao nhiêu? Ngưỡng cache của {model}: {entry['cache_min_tokens']} token")
    n = client.count_tokens(system=system_co_cache(), messages=[{"role": "user", "content": "x"}]).input_tokens
    print(f"   count_tokens: {n} token -> {'đủ' if n >= entry['cache_min_tokens'] else 'CHƯA đủ'} để cache")

    print("\n2) Bẫy: breakpoint trên block đổi mỗi lần (giờ hiện tại) -> lần nào cũng GHI cả prefix, không đọc")
    for gio in ("08:00", "08:01"):
        sai = [*system_co_cache(), {"type": "text", "text": f"Bây giờ là {gio}.",
                                    "cache_control": {"type": "ephemeral"}}]
        sai[1] = {k: v for k, v in sai[1].items() if k != "cache_control"}  # bỏ breakpoint đúng chỗ
        in_dong(f"giờ {gio}", client.create(system=sai, messages=[{"role": "user", "content": "Chào"}]))

    print("\n3) Đúng chỗ: breakpoint ở cuối phần không đổi; cùng sổ tay, ba câu hỏi khác nhau")
    for i, cau in enumerate(["Lò LN-1200 nóng tối đa bao nhiêu?", "Cân CP-220 đọc tới mấy mg?",
                             "Bao lâu hiệu chuẩn HV-200 một lần?"], 1):
        msg = client.create(system=system_co_cache(), messages=[{"role": "user", "content": cau}])
        in_dong(f"lần {i}" + (" (ghi cache)" if i == 1 else " (đọc cache)"), msg)

    print("\n4) Đổi effort khác mặc định -> có thể mất cache (docs: có thể mất phần messages, có model mất cả"
          "\n   tools và system; mock coi như mất hết)")
    msg = client.create(system=system_co_cache(), messages=[{"role": "user", "content": "Lò LN-1200?"}],
                        output_config={"effort": "low"})
    in_dong("effort=low", msg)

    print("\n5) Prompt ngắn hơn ngưỡng: không cache, KHÔNG báo lỗi")
    ngan = [{"type": "text", "text": "Trả lời ngắn.", "cache_control": {"type": "ephemeral"}}]
    in_dong("system ngắn", client.create(system=ngan, messages=[{"role": "user", "content": "Chào"}]))

    print("\n6) Cần đọc bao nhiêu lần để hoà vốn (giá trong config/models.yaml)")
    print(f"   {'model':<20}{'ghi 5m':>8}{'ghi 1h':>8}{'đọc':>7}{'hoà vốn 5m':>12}{'hoà vốn 1h':>12}")
    for m, e in load_models()["models"].items():
        if e.get("status") == "active" and e.get("cache_price_per_mtok"):
            c = e["cache_price_per_mtok"]
            print(f"   {m:<20}{c['write_5m']:>8}{c['write_1h']:>8}{c['read']:>7}"
                  f"{so_lan_doc_hoa_von(m, '5m'):>9} lần{so_lan_doc_hoa_von(m, '1h'):>9} lần")
    print("   Số token là của mock (1 token ≈ 4 ký tự), không phải số thật. Giá là giá thật trong config.")


if __name__ == "__main__":
    main()
