"""Module 06: Message Batches API: send many requests at once, get the results later, pay 50% of the price.

Use it when you do not need the answer right away (grading, labeling, summarizing in bulk). A batch usually
finishes within 1 hour; after at most 24 hours it expires. The results do NOT come back in the order you sent
them: match them by custom_id.

Run:  CLAUDE_MOCK=1 uv run python en/modules/06-cost/python/04_batch.py
Real run: the script waits at most CHO_TOI_DA_S seconds; if the batch is not done, it prints the batch id
so you can get the results later.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))

from claude_vi import ClaudeVi, estimate_cost_usd, text_of  # noqa: E402

CHO_TOI_DA_S = 600      # the longest wait, in seconds
NGHI_GIUA_LAN_S = 30    # the pause between two status checks, in seconds

QUESTIONS = [
    "What is a micro hardness tester used for? One sentence.",
    "Why measure a blank before UV-Vis spectroscopy? One sentence.",
    "How is an analytical balance different from a precision balance? One sentence.",
    "Why does a furnace need a protective gas? One sentence.",
]


def tao_requests(cau_hoi: list[str], model: str | None = None) -> list[dict]:
    """Build the requests (tao = build): one request per question (cau_hoi).

    custom_id: 1–64 characters, letters, digits, '-' or '_', unique within the batch.
    """
    params = {"model": model} if model else {}
    return [{"custom_id": f"cau-{i:03d}", "params": {**params, "messages": [{"role": "user", "content": c}]}}
            for i, c in enumerate(cau_hoi)]


def cho_xong(client: ClaudeVi, batch_id: str, cho_toi_da_s: float, nghi_s: float):
    """Wait until done (cho xong): check the status until processing_status == "ended" or time runs out."""
    start = time.monotonic()
    while True:
        batch = client.batch_retrieve(batch_id)
        print(f"   {batch.processing_status:<12} processing {batch.request_counts.processing}")
        if batch.processing_status == "ended" or time.monotonic() - start > cho_toi_da_s:
            return batch
        time.sleep(nghi_s)


def gom_ket_qua(ket_qua) -> dict[str, dict]:
    """Group the results (gom ket qua): custom_id -> {"loai" (type), "text", "usd"}.

    Only "succeeded" is billed, at the batch price.
    """
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
    requests = tao_requests(QUESTIONS)

    print(f"1) Send a batch of {len(requests)} requests (claude_vi checks the rules of each request BEFORE"
          "\n   sending: the API reports bad params only when the whole batch is done)")
    batch = client.batch_create(requests)
    hours = (batch.expires_at - batch.created_at).total_seconds() / 3600
    print(f"   {batch.id}: {batch.processing_status}, expires {hours:.0f} hours after creation if not done")

    print("\n2) Wait for the batch to finish")
    mock = client.settings.mock
    batch = cho_xong(client, batch.id, CHO_TOI_DA_S, 0 if mock else NGHI_GIUA_LAN_S)
    if batch.processing_status != "ended":
        print(f"   Not done after {CHO_TOI_DA_S} seconds. Get the results later with"
              f" client.batch_results('{batch.id}').")
        return
    print(f"   Done: {batch.request_counts.succeeded} succeeded, {batch.request_counts.errored} errored")

    print("\n3) In what order do the results come back?")
    results = list(client.batch_results(batch.id))
    print(f"   {[r.custom_id for r in results]}")
    print("   The API does not guarantee the order (the mock reverses it on purpose):"
          " always match by custom_id")

    print("\n4) Match with the questions, bill at the batch price")
    grouped = gom_ket_qua(results)
    for req, question in zip(requests, QUESTIONS):
        res = grouped[req["custom_id"]]
        print(f"   {req['custom_id']} {res['loai']:<9} ${res['usd']:.7f}  {question[:40]}")
    batch_usd = sum(res["usd"] for res in grouped.values())
    normal_usd = sum(estimate_cost_usd(r.result.message) for r in results if r.result.type == "succeeded")
    print(f"   Total ${batch_usd:.7f}; the same requests as normal calls: ${normal_usd:.7f}"
          " (batch = 50% of the standard price)")


if __name__ == "__main__":
    main()
