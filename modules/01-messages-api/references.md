# Nguồn · Module 01

Mọi dữ kiện về API, giá và hành vi model trong module này được kiểm ngày **24/10/2026** từ các nguồn dưới đây. Nội dung bài viết bằng lời của repo, không sao chép.

| Chủ đề | Nguồn | Dùng cho |
|---|---|---|
| Request, hội thoại nhiều lượt, prefill bị bỏ, message `system` giữa hội thoại | [Using the Messages API](https://platform.claude.com/docs/en/build-with-claude/working-with-messages) | Mục 1, 2, "Điều gì đã thay đổi" |
| Tham chiếu đầy đủ tham số | [Messages API reference](https://platform.claude.com/docs/en/api/messages/create) | Mục 1 |
| Các giá trị `stop_reason`, `stop_details` | [Handling stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons) | Mục 4, bài 2 |
| Thinking bật sẵn, `display` mặc định `"omitted"`, thinking tính là output token và vào `max_tokens`; tắt thinking theo từng model | [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) | Mục 3, 5, "Điều gì đã thay đổi" |
| Mã lỗi, `request-id`, SDK tự retry 2 lần và tôn trọng `retry-after`, lỗi thinking block bị sửa / gắn với hội thoại khác | [Claude API errors](https://platform.claude.com/docs/en/api/errors) | Mục 7, bài 3 |
| Giới hạn kích thước request Messages API tăng từ 32 MB lên 128 MB trên Claude API (kiểm 09/11/2026) | [Release notes 28/10/2026](https://platform.claude.com/docs/en/release-notes/overview), [Request size limits](https://platform.claude.com/docs/en/api/overview#request-size-limits) | Mục 7 |
| Thứ tự event SSE, `usage` cộng dồn, `thinking_delta` / `signature_delta`, event `error` giữa stream | [Streaming messages](https://platform.claude.com/docs/en/build-with-claude/streaming) | Mục 6 |
| Giá theo MTok; Haiku 5.5 có giá cao hơn khi prompt trên 100.000 token | [Pricing](https://platform.claude.com/docs/en/about-claude/pricing) | Mục 5, chi phí ước tính |
| Rate limit, spend limit | [Rate limits](https://platform.claude.com/docs/en/api/rate-limits) | Mục 7 |
| Kiểu dữ liệu `Message`, `RawMessageStreamEvent`, `OutputTokensDetails.thinking_tokens`, các lớp lỗi | `anthropic` Python SDK 1.17.0 (đọc mã nguồn đã cài) | Mock, test |

## Giá đã kiểm (24/10/2026, USD / triệu token)

| Model | Input | Output |
|---|---|---|
| `claude-haiku-5-5` (prompt ≤ 100.000 token) | 0,10 | 0,50 |
| `claude-sonnet-5-5` | 2 | 10 |
| `claude-opus-5-5` | 4 | 20 |
| `claude-fable-5-1` | 10 | 50 |

Khớp với `price_per_mtok` trong [`config/models.yaml`](../../config/models.yaml). Giá có thể đổi; kiểm lại trang Pricing trước khi trích dẫn.

## Ghi chú khi kiểm

- Docs nhắc API version `2026-10-21` (từ version này, gửi `temperature`/`top_p`/`top_k` với **bất kỳ** giá trị nào cũng lỗi). SDK 1.17.0 vẫn gửi header `anthropic-version: 2023-06-01`; module này không đổi version.
- Trang Thinking xác nhận Haiku 5.5 nhận `thinking: {"type": "disabled"}` ở effort `high` trở xuống — khớp giả định `thinking_disabled_allowed: true` trong `config/models.yaml`.
