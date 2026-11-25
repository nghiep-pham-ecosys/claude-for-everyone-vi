# Nguồn · Module 06

Kiểm ngày **25/11/2026** (mục 1–4 dùng lại dữ kiện đã kiểm ở module 01 và 07, ghi ngày riêng). Nội dung bài viết bằng lời của repo.

| Chủ đề | Nguồn | Kiểm ngày | Dùng cho |
|---|---|---|---|
| Giá input/output theo MTok của 5 model active, khớp `price_per_mtok` trong config | [Pricing, Model pricing](https://platform.claude.com/docs/en/about-claude/pricing#model-pricing) | 25/11/2026 | Mục 2, script 01 |
| Giá ghi cache 5 phút (1,25x), 1 giờ (2x), đọc cache theo model (0,1x; 0,05x Opus 5.5 và Sonnet 5.5; 0,025x Fable 5.2 và 5.1); hoà vốn sau 1 lần đọc (5 phút) và 2 lần đọc (1 giờ); giá cache nhân chồng với batch và data residency | [Pricing, Prompt caching](https://platform.claude.com/docs/en/about-claude/pricing#prompt-caching), [Prompt caching, Pricing](https://platform.claude.com/docs/en/build-with-claude/prompt-caching#pricing) | 25/11/2026 | Mục 5, `cache_price_per_mtok` trong config, script 02, bài 1 |
| Haiku 5.5: prompt trên 100.000 token trả giá cao hơn cho mọi loại token, độ dài tính cả token đọc/ghi cache | [Pricing, Long context pricing](https://platform.claude.com/docs/en/about-claude/pricing#long-context-pricing) | 25/11/2026 | Mục 5, `long_context` trong config, `estimate_cost_usd` |
| `inference_geo` "us": 1,1x mọi loại token trên model 4.6 trở đi | [Pricing, Data residency pricing](https://platform.claude.com/docs/en/about-claude/pricing#data-residency-pricing) | 25/11/2026 | Bẫy thường gặp |
| Cách cache hoạt động: prefix tools → system → messages, `cache_control`, `ttl` "5m"/"1h", làm mới khi đọc trúng, tối đa 4 breakpoint, dò ngược 20 block, chỉ ghi ở breakpoint, ngưỡng 512 token cho 5 model active, dưới ngưỡng không lỗi, automatic caching, trộn TTL (1h trước 5m), những gì làm mất cache (effort, thinking, effort bằng mặc định thì không mất), các trường `usage` và công thức tổng input, cache chỉ dùng được sau khi response đầu bắt đầu, không xoá cache bằng tay | [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) | 25/11/2026 | Mục 5, `_cache_usage` trong mock, `cache_control_errors` trong `claude_vi.rules`, `cache_min_tokens` trong config |
| `CacheControlEphemeralParam.ttl` nhận `"5m"`/`"1h"`; `Usage.cache_creation` (`ephemeral_5m_input_tokens`, `ephemeral_1h_input_tokens`); `cache_control` cấp cao nhất trên `messages.create` | `anthropic` Python SDK 1.17.0 (đọc kiểu dữ liệu đã cài); [API Messages create](https://platform.claude.com/docs/en/api/messages/create) | 25/11/2026 | Mục 5, script 02 |
| `count_tokens`: tham số, `MessageTokensCount.input_tokens`, miễn phí, giới hạn request riêng, là ước tính, không dùng cache, không nhận server tool (trừ advisor tool), MCP connector, ảnh/PDF qua `url` hoặc `file`; tokenizer mới khoảng 30% token nhiều hơn từ model 4.7 (Opus 5.5 tới khoảng 35%, theo migration guide) | [Token counting](https://platform.claude.com/docs/en/build-with-claude/token-counting), [API count_tokens](https://platform.claude.com/docs/en/api/messages/count_tokens) | 25/11/2026 | Mục 6, script 03, bài 2 |
| Opus 5.5, Sonnet 5.5, Fable 5.2 trả 400 với `tool_choice` any/tool kể cả khi đếm token | [Opus 5.5 migration guide](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide#forced-tool-use-is-not-supported), [Sonnet 5.5 migration guide](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide#forced-tool-use-is-not-supported), [Fable 5.2 migration guide](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide) | 25/11/2026 | Mục 6 |
| Batch: giảm 50% input và output, 100.000 request hoặc 256 MB, đa số xong trong 1 giờ, hết hạn sau 24 giờ, kết quả giữ 29 ngày, luật `custom_id`, `params` kiểm bất đồng bộ, `processing_status`, `request_counts`, loại kết quả và loại nào tính tiền, thứ tự không bảo đảm, huỷ, tham số không dùng được (`stream`, `speed`, `fallbacks`, `max_tokens: 0`), cache trong batch best-effort (30–98%), khuyên cache 1 giờ | [Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing), [Pricing, Batch processing](https://platform.claude.com/docs/en/about-claude/pricing#batch-processing), [Pricing FAQ](https://platform.claude.com/docs/en/about-claude/pricing#how-do-discounts-stack) | 25/11/2026 | Mục 7, `batch_price_multiplier` trong config, `_MockBatches`, script 04, bài 3 |
| `client.messages.batches` (`create`, `retrieve`, `results`, `cancel`), `MessageBatch`, `MessageBatchIndividualResponse`, `results()` báo lỗi khi chưa có `results_url` | `anthropic` Python SDK 1.17.0 | 25/11/2026 | `ClaudeVi.batch_*`, mock |
| Message threads: ra mắt beta 02/11/2026, header `message-threads-2026-08-12`, create/continue, gửi gì ở mỗi request (create-only, cố định, tự do), tối đa 4 breakpoint, mỗi id continue một lần, best-effort, hết hạn 5 phút, các lý do khác của 404, chỉ gửi lại khi mã là `thread_not_found`, ứng dụng là nguồn sự thật, không tự cache (dùng `cache_control` cấp cao nhất), giá không đổi, không dùng với batch và token counting, không ZDR, mã lỗi | [Message threads](https://platform.claude.com/docs/en/build-with-claude/message-threads), [Release notes 02/11/2026](https://platform.claude.com/docs/en/release-notes/overview#november-2-2026) | 25/11/2026 | Mục 8, `_respond_thread` trong mock, script 05 |
| SDK 1.17.0 chưa có tham số `thread`; `claude_vi` gửi qua `extra_body` | `anthropic` Python SDK 1.17.0 (không có `beta.messages.thread`) | 25/11/2026 | Mục 8 |
| `input_tokens`, `output_tokens` gồm thinking, `thinking_tokens` | [module 01 references](../01-messages-api/references.md) (Thinking) | 24/10/2026 | Mục 1, 4 |
| `max_tokens` là trần cứng cho thinking + text; effort là tín hiệu mềm; thinking cũ giữ lại trong context; message `system` giữa hội thoại giữ cache | [module 07 references](../07-thinking/references.md) | 09/11/2026 | Mục 3, 4, 5 |

## Chưa kiểm hoặc là suy luận

- Docs Message threads không nói rõ phần hội thoại cũ được tính tiền thế nào ở request continue, chỉ ghi "Threads do not change pricing or rate limits". Mock giả định phần cũ vẫn tính là input. Cần đo khi chạy thật.
- Tỉ lệ đổi giữa ký tự và token của mock (1 token ≈ 4 ký tự) là quy ước của repo, không phải số của tokenizer thật.
- Kết quả batch thật có ghi `usage.service_tier = "batch"` hay không: chưa kiểm, nên `estimate_cost_usd` nhận `batch=True` thay vì đọc trường này.
- Bản SDK nào có helper `client.beta.messages.thread(...)`: chưa kiểm. Bản 1.17.0 đã cài thì chưa có.

## Chi phí ước tính

5 script, 17 lời gọi tạo message và một batch 4 request tới model mặc định với `MAX_TOKENS=1024` (01: 2, 02: 7, 03: 2, 04: batch 4 request, 05: 6; phần giả lập hết hạn của 05 chỉ chạy ở mock). Các lời gọi `count_tokens` miễn phí. Trường hợp xấu nhất với Haiku 5.5:

- Output: 17 × 1.024 × $0,50/MTok + 4 × 1.024 × $0,25/MTok (batch) ≈ $0,010.
- Input: sổ tay khoảng 1.000–2.000 token mỗi lời gọi, phần lớn tính theo giá ghi cache $0,125/MTok hoặc đọc cache $0,01/MTok; dưới $0,005.

Cả module dưới $0,02. Script 04 chờ batch tối đa 10 phút; chưa xong thì in id để lấy kết quả sau. Đây là ước tính, chưa đo bằng API thật.
