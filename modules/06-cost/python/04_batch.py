"""Module 06 — Message Batches API: gửi nhiều request một lần, nhận kết quả sau, trả 50% giá.

Dùng khi không cần câu trả lời ngay (chấm bài, gắn nhãn, tóm tắt hàng loạt). Batch thường xong trong 1 giờ,
tối đa 24 giờ thì hết hạn. Kết quả KHÔNG theo thứ tự gửi: ghép bằng custom_id.

Chạy:  CLAUDE_MOCK=1 uv run python modules/06-cost/python/04_batch.py
Chạy thật: script chờ tối đa CHO_TOI_DA_S giây; chưa xong thì in id batch để lấy kết quả sau.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from claude_vi import ClaudeVi, estimate_cost_usd, text_of  # noqa: E402

CHO_TOI_DA_S = 600
NGHI_GIUA_LAN_S = 30

CAU_HOI = [
    "Máy đo độ cứng vi mô dùng để làm gì? Một câu.",
    "Vì sao cần đo nền trước khi đo quang phổ UV-Vis? Một câu.",
    "Cân phân tích khác cân kỹ thuật ở điểm nào? Một câu.",
    "Vì sao lò nung cần khí bảo vệ? Một câu.",
]


def tao_requests(cau_hoi: list[str], model: str | None = None) -> list[dict]:
    """Mỗi câu hỏi một request. custom_id: 1–64 ký tự chữ, số, '-' hoặc '_', không trùng trong batch."""
    params = {"model": model} if model else {}
    return [{"custom_id": f"cau-{i:03d}", "params": {**params, "messages": [{"role": "user", "content": c}]}}
            for i, c in enumerate(cau_hoi)]


def cho_xong(client: ClaudeVi, batch_id: str, cho_toi_da_s: float, nghi_s: float):
    """Hỏi trạng thái tới khi processing_status == "ended" hoặc hết thời gian chờ."""
    bat_dau = time.monotonic()
    while True:
        batch = client.batch_retrieve(batch_id)
        print(f"   {batch.processing_status:<12} đang xử lý {batch.request_counts.processing}")
        if batch.processing_status == "ended" or time.monotonic() - bat_dau > cho_toi_da_s:
            return batch
        time.sleep(nghi_s)


def gom_ket_qua(ket_qua) -> dict[str, dict]:
    """custom_id -> {"loai", "text", "usd"}. Chỉ "succeeded" bị tính tiền, theo giá batch."""
    out = {}
    for r in ket_qua:
        if r.result.type == "succeeded":
            msg = r.result.message
            out[r.custom_id] = {"loai": "succeeded", "text": text_of(msg),
                                "usd": estimate_cost_usd(msg, batch=True)}
        elif r.result.type == "errored":
            out[r.custom_id] = {"loai": "errored", "text": r.result.error.error.message, "usd": 0.0}
        else:  # canceled, expired
            out[r.custom_id] = {"loai": r.result.type, "text": "", "usd": 0.0}
    return out


def main() -> None:
    client = ClaudeVi()
    requests = tao_requests(CAU_HOI)

    print(f"1) Gửi batch {len(requests)} request (claude_vi kiểm luật từng request TRƯỚC khi gửi: API chỉ báo lỗi"
          "\n   params khi cả batch đã xong)")
    batch = client.batch_create(requests)
    han = (batch.expires_at - batch.created_at).total_seconds() / 3600
    print(f"   {batch.id}: {batch.processing_status}, hết hạn {han:.0f} giờ sau khi tạo nếu chưa xong")

    print("\n2) Chờ batch xong")
    mock = client.settings.mock
    batch = cho_xong(client, batch.id, CHO_TOI_DA_S, 0 if mock else NGHI_GIUA_LAN_S)
    if batch.processing_status != "ended":
        print(f"   Chưa xong sau {CHO_TOI_DA_S} giây. Lấy kết quả sau bằng client.batch_results('{batch.id}').")
        return
    print(f"   Xong: {batch.request_counts.succeeded} succeeded, {batch.request_counts.errored} errored")

    print("\n3) Kết quả về theo thứ tự nào?")
    ket_qua = list(client.batch_results(batch.id))
    print(f"   {[r.custom_id for r in ket_qua]}")
    print("   API không bảo đảm thứ tự (mock cố ý đảo ngược): luôn ghép bằng custom_id")

    print("\n4) Ghép với câu hỏi, tính tiền theo giá batch")
    gom = gom_ket_qua(ket_qua)
    for req, cau in zip(requests, CAU_HOI):
        kq = gom[req["custom_id"]]
        print(f"   {req['custom_id']} {kq['loai']:<9} ${kq['usd']:.7f}  {cau[:40]}")
    batch_usd = sum(kq["usd"] for kq in gom.values())
    thuong_usd = sum(estimate_cost_usd(r.result.message) for r in ket_qua if r.result.type == "succeeded")
    print(f"   Tổng ${batch_usd:.7f}; cùng request gọi thường: ${thuong_usd:.7f} (batch = 50% giá chuẩn)")


if __name__ == "__main__":
    main()
