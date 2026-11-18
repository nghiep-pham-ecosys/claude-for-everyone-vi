# Nguồn · Module 08

Kiểm ngày **18/11/2026**, trừ khi ghi khác. Nội dung bài viết bằng lời của repo.

| Chủ đề | Nguồn | Ngày kiểm | Dùng cho |
|---|---|---|---|
| Định nghĩa workflow (đường đi định sẵn trong code) và agent (LLM tự điều khiển quá trình và tool); năm mẫu: prompt chaining có cổng kiểm bằng code, routing, parallelization (sectioning, voting), orchestrator-workers, evaluator-optimizer; tìm giải pháp đơn giản nhất, chỉ thêm độ phức tạp khi cần; agent dùng giới hạn số vòng lặp để giữ kiểm soát. Bài đăng 19/12/2024, trang ghi chú nhiều công cụ đã thay đổi từ đó | [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) | 18/11/2026 | Mục 1–4, script 01–06 |
| Đặt tiền tố tên tool; trả ngữ cảnh có ý nghĩa; giới hạn độ dài kết quả tool; lời nhắn lỗi nói rõ sai gì và sửa thế nào | [Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) | 18/11/2026 | Mục 5–6, mô tả tool trong `phong_thi_nghiem.py` |
| `tool_result` đứng ngay sau `tool_use` và đứng đầu content; thiếu `tool_result` là lỗi; `is_error` với lời nhắn có ích; kết quả tool là nội dung không đáng tin (indirect prompt injection), giữ trong `tool_result`, không đặt vào `system` hay text của user | [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) | 18/11/2026 | Mục 5–6, script 07–08, bài 3 |
| Thinking tính vào `max_tokens` và tính tiền là output; `max_tokens` là trần cứng, effort chỉ là hướng dẫn; trong vòng tool phải gửi lại block thinking nguyên vẹn; interleaved thinking tự động với adaptive thinking; khi dừng ở `max_tokens` ngay sau một lần gọi tool, muốn tiếp thì gửi lại lượt assistant nguyên vẹn | [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) | 18/11/2026 | Mục 5, bảng "Điều gì đã thay đổi" |
| Block thinking gắn với `system`, `tools` và mọi message trước nó (prefix check); chỉ nối thêm vào hội thoại; nội dung không đáng tin chỉ gửi trong `tool_result` | [Preserved thinking](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking) | 18/11/2026 | Mục 5, bài 3 |
| Message `role: "system"` giữa hội thoại: không cần beta header; phải đứng ngay sau lượt user và trước lượt assistant hoặc ở cuối; trong vòng lặp agent đặt sau lượt user mang `tool_result`; Sonnet 5.5 và Haiku 5.5 giữ lời nhắc của chương trình ở message `system` riêng, lời của người dùng đặt sau `tool_result` trong lượt user; không đặt dữ liệu bên ngoài vào message `system` | [Mid-conversation system messages](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages) | 18/11/2026 | Mục 5–6, script 07 |
| Quản lý context cho agent chạy lâu: context editing (beta, `context-management-2025-06-27`), xoá kết quả tool cũ (`clear_tool_uses_20250919`) và block thinking cũ (`clear_thinking_20251015`) ở phía server; server-side compaction là cách chính cho hội thoại dài | [Context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing) | 18/11/2026 | Ghi chú cuối mục 5 (chỉ giới thiệu; `claude_vi` chưa hỗ trợ) |
| Thinking block gắn với tài khoản và lịch sử hội thoại; ảnh hưởng tới vòng tool tự viết ở module 03 và 08 | [docs/kiem-chung-2026-10-21.md](../../docs/kiem-chung-2026-10-21.md), điểm 2 | 21/10/2026 (tài liệu trong repo) | Mục 5 |
| Luật `tool_choice` theo model, `between_tools` chỉ trên Sonnet 5.5, prefix check theo ngày tạo tài khoản | [`config/models.yaml`](../../config/models.yaml), [module 03 references](../03-tool-use/references.md), [module 07 references](../07-thinking/references.md) | theo ngày ghi ở từng file | Mục 5, bảng "Điều gì đã thay đổi" |

Chưa kiểm: docs SDK Python về việc dùng chung một client giữa nhiều luồng. Vì vậy script 04 dùng một `ClaudeVi` cho mỗi nhánh.

## Chi phí ước tính

8 script, tối đa khoảng 51 lời gọi tới model mặc định khi chạy thật (01: 3; 02: 3; 03: 8; 04: 6; 05: 6; 06: 6; 07: 9; 08: 10). Số lời gọi ở 03, 05, 07, 08 phụ thuộc vào việc Claude gọi bao nhiêu tool, nên đây là trường hợp xấu nhất theo trần lượt trong code. Ở mock mode cả module là 40 lời gọi.

Output trường hợp xấu nhất với Haiku 5.5 và `MAX_TOKENS=1024`: 51 × 1.024 × $0,50/MTok ≈ $0,026. Input: nếu mỗi lời gọi tới khoảng 3.000 token (trang sổ tay, định nghĩa tool, lịch sử dài dần), 51 × 3.000 × $0,10/MTok ≈ $0,015. Cả module dưới $0,05. Giá đọc từ `config/models.yaml` (giá "from" của Haiku 5.5). Đây là ước tính, chưa đo bằng API thật.
