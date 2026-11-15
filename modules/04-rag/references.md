# Nguồn · Module 04

Kiểm ngày **09/11/2026**. Nội dung bài viết bằng lời của repo. Công thức BM25 là kiến thức chung của ngành tìm kiếm thông tin; repo dùng dạng idf `ln(1 + (N − n + 0,5)/(n + 0,5))` (không âm), như nhiều thư viện tìm kiếm phổ biến.

| Chủ đề | Nguồn | Dùng cho |
|---|---|---|
| Block `search_result`: trường bắt buộc, chỉ chứa text, đặt ở lượt user hoặc trong `tool_result`; `tool_result` có `search_result` thì toàn bộ phải là `search_result`; citations tất cả hoặc không; `search_result_location` (`source`, `title`, `search_result_index`, chỉ số khối, `cited_text` không tính token); trích nguyên khối; không tìm thấy thì trả text thay vì lỗi; prompt "chỉ JSON" làm mất trích dẫn | [Search results](https://platform.claude.com/docs/en/build-with-claude/search-results) | Mục 6, script 04–05, bài 3, `claude_vi.rules.search_result_errors`, `_search_payload` trong mock |
| Kho dưới khoảng 200.000 token có thể gửi cả; BM25 mạnh với mã và thuật ngữ chính xác; embedding + BM25 tốt hơn embedding đơn lẻ; contextual retrieval (ngữ cảnh 50–100 token mỗi đoạn); tỉ lệ tìm hụt top-20 5,7% → 2,9% (ngữ cảnh cho cả embedding và BM25) → 1,9% (thêm rerank); top-20 tốt hơn top-5/10; rank fusion | [Introducing Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) (Anthropic, 2024) | "Vì sao học cái này", mục 2, 4, 5 |
| Anthropic không có model embedding riêng; giới thiệu nhà cung cấp bên ngoài | [Embeddings](https://platform.claude.com/docs/en/build-with-claude/embeddings) | Mục 7 |
| `tool_choice` any/tool trả 400 trên Opus 5.5, Sonnet 5.5, Fable 5.1, Fable 5.2 | [Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools), [Fable 5.2 migration guide](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide) | Mục 6, script 05 |
| Chuẩn hoá Unicode NFC/NFD, category `Mn` | [Python `unicodedata`](https://docs.python.org/3/library/unicodedata.html) | Mục 2, bài 1 |

Số liệu trong bài blog đo năm 2024 trên dữ liệu của Anthropic, với Claude 3 Haiku sinh ngữ cảnh. Bài học chỉ dẫn lại để minh hoạ hướng cải thiện, không khẳng định kết quả tương tự trên kho khác.

## Chi phí ước tính

Script 01–02 không gọi API. Script 03: 4 lời gọi, `max_tokens` 256, mỗi lời gọi gửi một tài liệu ngắn (dưới 1.000 token). Script 04: 1 lời gọi. Script 05: 2–4 lời gọi. Output trường hợp xấu nhất với Haiku 5.5: (4 × 256 + 5 × 1.024) × $0,50/MTok ≈ $0,003; input dưới 20.000 token ≈ $0,002. Cả module dưới $0,01. Đây là ước tính, chưa đo bằng API thật.
