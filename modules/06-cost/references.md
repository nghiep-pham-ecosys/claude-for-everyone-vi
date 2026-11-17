# Nguồn · Module 06 (phần cơ bản)

Phần này **không thêm dữ kiện mới** về giá hay hành vi model. Mọi dữ kiện lấy từ các nguồn đã kiểm ở module khác hoặc từ mã nguồn đã cài. Nội dung bài viết bằng lời của repo.

| Chủ đề | Nguồn | Kiểm ngày | Dùng cho |
|---|---|---|---|
| Giá input/output theo MTok của từng model | `price_per_mtok` trong [`config/models.yaml`](../../config/models.yaml); trang [Pricing](https://platform.claude.com/docs/en/about-claude/pricing) đã kiểm ở [module 01](../01-messages-api/references.md) | 24/10/2026 (Fable 5.2: 09/11/2026, [module 07](../07-thinking/references.md)) | Mục 2, script |
| Giá Haiku 5.5 là mức "from"; cao hơn khi prompt trên 100.000 token | Ghi chú trong `config/models.yaml`; [module 01 references](../01-messages-api/references.md) | 24/10/2026 | Mục 2, Bẫy thường gặp |
| `input_tokens`, `output_tokens` gồm thinking, `thinking_tokens` | [module 01 references](../01-messages-api/references.md) (Thinking) | 24/10/2026 | Mục 1, 4 |
| `max_tokens` là trần cứng cho thinking + text; effort là tín hiệu mềm; đổi effort làm mất cache; thinking cũ giữ lại trong context | [module 07 references](../07-thinking/references.md) (Thinking, Effort) | 09/11/2026 | Mục 3, 4, 5 |
| Message `system` giữa hội thoại giữ được cache | [module 07 references](../07-thinking/references.md) (Mid-conversation system messages) | 09/11/2026 | Mục 5 |
| `Usage.cache_creation_input_tokens`, `Usage.cache_read_input_tokens`, `client.messages.count_tokens` | `anthropic` Python SDK 1.17.0 (đọc kiểu dữ liệu đã cài) | 17/11/2026 | Mục 3, 5, script |

## Chưa kiểm, để phần sau

- Giá ghi cache và đọc cache theo từng model. Chưa có trong `config/models.yaml`; cần kiểm trang Pricing rồi thêm vào config trước khi `estimate_cost_usd` tính được.
- Thời gian sống của cache, số token tối thiểu để cache, cách đánh dấu `cache_control`.
- Đếm token bằng API, giá Batch API, message threads (beta).

## Chi phí ước tính

1 script, 2 lời gọi tới model mặc định với `MAX_TOKENS=1024`. Output trường hợp xấu nhất với Haiku 5.5: 2 × 1.024 × $0,50/MTok ≈ $0,001; input không đáng kể. Dưới $0,01. Đây là ước tính, chưa đo bằng API thật.
