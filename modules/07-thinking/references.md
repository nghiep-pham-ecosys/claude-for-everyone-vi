# Nguồn · Module 07

Kiểm ngày **09/11/2026**. Nội dung bài viết bằng lời của repo.

| Chủ đề | Nguồn | Dùng cho |
|---|---|---|
| Thinking là gì, `signature`, tính là output token và vào `max_tokens`; bảng cấu hình theo model (`adaptive`/`enabled`/`between_tools`/`disabled`); `display` (`summarized`, `omitted`, `updates` beta), tóm tắt do model khác viết và tính tiền theo thinking gốc; `reasoning_extraction`; stream (`thinking_delta`, `signature_delta`, `get_final_message`); thinking với tool (một lượt assistant, giữ block, không đổi cấu hình giữa lượt, interleaved, progress updates); giữ block theo model; `redacted_thinking`; giới hạn output; SDK bắt stream khi `max_tokens` > 21.333 | [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) | Mục 1–6, script 01–04, luật `display`/`between_tools` trong `claude_vi.rules` |
| 5 mức effort, mặc định từng model (gồm Fable 5.2), effort ảnh hưởng mọi token output, không phải ngân sách cứng, effort theo message (beta), đổi effort làm mất cache | [Effort](https://platform.claude.com/docs/en/build-with-claude/effort) | Mục 4 |
| Prefix check (system, tools, message trước block); bảng lỗi theo model và ngày tạo tài khoản (31/8/2026); thông báo lỗi 400; `block_binding` (beta); những gì tính là sửa prefix và cách thay; bỏ block cũ nhất được, bỏ ở giữa thì hỏng; block gắn với tài khoản | [Preserved thinking](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking) | Mục 7, script 05, bài 3, `_check_prefix` trong mock |
| Message `role: "system"` giữa hội thoại: model hỗ trợ, không cần beta header, luật vị trí, không đặt dữ liệu ngoài vào đó | [Mid-conversation system messages](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages) | Mục 7, `claude_vi.rules.system_message_errors` |
| Lỗi 400 thường gặp về thinking | [Troubleshooting thinking](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting) | Bẫy thường gặp |
| Claude Fable 5.2 ra mắt: giá $8/$40 mỗi MTok, adaptive thinking luôn bật, prefix check cho mọi tài khoản, block gắn với tài khoản | [Release notes 09/11/2026](https://platform.claude.com/docs/en/release-notes/overview), [Fable 5.2 migration guide](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide) | `config/models.yaml`, bảng mục 3 |

## Chi phí ước tính

5 script, 11 lời gọi tới model mặc định (01: 2, 02: 1, 03: 4 với 3 lời gọi có `max_tokens` ≤ 16, 04: 1, 05: 3). Script 02 kiểm các model khác tại máy, không gửi request. Output trường hợp xấu nhất với Haiku 5.5: 8 × 1.024 × $0,50/MTok ≈ $0,004; input không đáng kể. Cả module dưới $0,01. Đây là ước tính, chưa đo bằng API thật.

Script 05 cố ý gửi một request sai. Trên tài khoản tạo từ 31/8/2026 nó trả 400 và không tốn token output.
