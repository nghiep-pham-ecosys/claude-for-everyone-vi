"""Module 06 — đếm token TRƯỚC khi gọi bằng count_tokens, rồi chặn request vượt ngân sách.

count_tokens nhận gần như cùng tham số với create (system, tools, messages, thinking...) nhưng KHÔNG có max_tokens,
không tạo message, không dùng cache và miễn phí (có giới hạn số request mỗi phút riêng).

Chạy:  CLAUDE_MOCK=1 uv run python modules/06-cost/python/03_dem_token.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from claude_vi import ClaudeVi, estimate_cost_usd, load_models  # noqa: E402

MTOK = 1_000_000
SO_TAY = (Path(__file__).resolve().parents[1] / "data" / "so_tay_thiet_bi.md").read_text("utf-8")
NGAN_SACH_USD = 0.001  # trần cho MỘT request trong ví dụ

TRA_THIET_BI = {
    "name": "tra_lich_thiet_bi",
    "description": "Tra lịch đặt trước của một thiết bị trong phòng thí nghiệm theo ngày.",
    "input_schema": {
        "type": "object",
        "properties": {"ma_thiet_bi": {"type": "string"}, "ngay": {"type": "string", "format": "date"}},
        "required": ["ma_thiet_bi", "ngay"],
        "additionalProperties": False,
    },
}


def uoc_tinh_truoc(client: ClaudeVi, params: dict) -> dict:
    """Đếm input bằng API, cộng trần output (max_tokens). Không tính cache: trường hợp xấu nhất."""
    params = dict(params)
    max_tokens = params.pop("max_tokens", client.settings.max_tokens)
    model = params.setdefault("model", client.settings.model)
    gia = load_models()["models"][model]["price_per_mtok"]
    n = client.count_tokens(**params).input_tokens
    return {
        "input_tokens": n,
        "input_usd": n * gia["input"] / MTOK,
        "tran_output_usd": max_tokens * gia["output"] / MTOK,
        "toi_da_usd": (n * gia["input"] + max_tokens * gia["output"]) / MTOK,
    }


def main() -> None:
    client = ClaudeVi()
    hoi = [{"role": "user", "content": "Lò LN-1200 nóng tối đa bao nhiêu độ?"}]

    print("1) Cùng câu hỏi, thêm dần ngữ cảnh: input tăng theo system và định nghĩa tool")
    cac_bien_the = {
        "chỉ câu hỏi": {"messages": hoi},
        "+ system sổ tay": {"system": SO_TAY, "messages": hoi},
        "+ system + 1 tool": {"system": SO_TAY, "tools": [TRA_THIET_BI], "messages": hoi},
    }
    for ten, params in cac_bien_the.items():
        print(f"   {ten:<20} {client.count_tokens(**params).input_tokens:>5} token")

    print(f"\n2) Chặn trước khi gọi: trần mỗi request ${NGAN_SACH_USD}")
    for max_tokens in (1024, 4096):
        params = {"system": SO_TAY, "messages": hoi, "max_tokens": max_tokens}
        u = uoc_tinh_truoc(client, params)
        gui = u["toi_da_usd"] <= NGAN_SACH_USD
        print(f"   max_tokens={max_tokens:<5} input ${u['input_usd']:.6f} + trần output ${u['tran_output_usd']:.6f}"
              f" = tối đa ${u['toi_da_usd']:.6f} -> {'GỬI' if gui else 'KHÔNG gửi'}")
        if gui:
            msg = client.create(**params)
            print(f"   đã gửi, tốn thật ${estimate_cost_usd(msg):.6f} (dưới trần)")

    print("\n3) Sau khi gọi: so số đếm với usage (tổng input = input + ghi cache + đọc cache)")
    params = {"system": SO_TAY, "messages": hoi}
    dem = client.count_tokens(**params).input_tokens
    msg = client.create(**params)
    u = msg.usage
    that = u.input_tokens + (u.cache_creation_input_tokens or 0) + (u.cache_read_input_tokens or 0)
    print(f"   count_tokens {dem} | usage {that} | chi phí ${estimate_cost_usd(msg):.6f}")
    print("   API thật: số đếm là ước tính, có thể lệch chút ít; token do hệ thống thêm có thể được đếm nhưng"
          "\n   không bị tính tiền. Mock đếm theo quy ước 1 token ≈ 4 ký tự nên hai số trùng nhau.")

    print("\n4) Mỗi model một tokenizer: đếm lại bằng đúng model sẽ dùng")
    for m, e in load_models()["models"].items():
        if e.get("status") == "active":
            print(f"   {m:<20} {client.count_tokens(model=m, **params).input_tokens:>5} token")
    print("   Mock dùng chung một cách đếm. Docs: model 4.7 trở đi sinh nhiều hơn khoảng 30% token cho cùng"
          "\n   đoạn text so với model cũ, nên số đếm cũ không dùng lại được.")


if __name__ == "__main__":
    main()
