# Nguồn · Module 03

Kiểm ngày **24/10/2026**. Nội dung bài viết bằng lời của repo.

| Chủ đề | Nguồn | Dùng cho |
|---|---|---|
| Client tool và server tool; vòng tool use; `disable_parallel_tool_use`; tool runner; token system prompt cho tool (286 token với `auto`/`none` trên Haiku/Sonnet/Opus 5.5) | [Tool use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview) | Mục 1, 3, 6 |
| `name` khớp `^[a-zA-Z0-9_-]{1,128}$`; mô tả chi tiết là yếu tố quan trọng nhất (3–4 câu); gộp tool; tiền tố tên; `input_examples`; bảng `tool_choice`; Opus 5.5/Sonnet 5.5/Fable 5.1 từ chối any/tool; Haiku 5.5 nhận nhưng bỏ thinking | [Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools) | Mục 2, 5, bài 1, `claude_vi.rules.tool_errors` |
| Trường của `tool_use`/`tool_result`; `tool_result` đứng ngay sau và đứng đầu content; `is_error` với lời nhắn có ích; nội dung tool là dữ liệu không đáng tin | [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) | Mục 3, 6, bài 2 |
| `strict: true` đảm bảo input khớp schema; tối đa 20 tool strict; dùng chung giới hạn JSON Schema với structured outputs | [Strict tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use), [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) | Mục 2 |
| Block thinking ở lượt assistant mới nhất không được sửa; block gắn với phần hội thoại trước nó | [Claude API errors](https://platform.claude.com/docs/en/api/errors), [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) | Mục 4, script 05, kiểm tra trong mock |
| Thiết kế tool cho agent | [Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) | Đọc thêm |

## Chi phí ước tính

5 script, 11 lời gọi (01: 2, 02: 2, 03: 3, 04: 2, 05: 2 — một lời gọi ở 05 bị chặn ngay ở mock; ở API thật nó cũng trả 400 và không tốn token ra). Trường hợp xấu nhất với Haiku 5.5: 11 × 1.024 × $0,50/MTok ≈ $0,006, cộng input (khoảng 600–1.000 token mỗi lời gọi vì có định nghĩa tool, ≈ $0,001).
