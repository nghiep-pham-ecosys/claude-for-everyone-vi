# Nguồn · Module 02

Kiểm ngày **24/10/2026**. Nội dung bài viết bằng lời của repo; không sao chép từ `anthropics/courses` hay `prompt-eng-interactive-tutorial` (xem [NOTICE.md](../../NOTICE.md)).

| Chủ đề | Nguồn | Dùng cho |
|---|---|---|
| Khi nào nên làm prompt engineering; cần tiêu chí thành công và cách đo trước | [Prompt engineering overview](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview) | "Vì sao học cái này" |
| Rõ ràng/trực tiếp, thêm lý do, ví dụ (3–5, `<example>`), XML tag, vai trò, tài liệu dài ở trên + câu hỏi ở cuối (tới 30%), điều khiển định dạng, bỏ prefill, prompt chaining | [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) | Mục 1–5, 7 |
| `output_config.effort`, 5 mức, mặc định từng model, effort không phải ngân sách cứng, `adaptive` không phải mức effort | [Effort](https://platform.claude.com/docs/en/build-with-claude/effort) | Mục 6, `config/models.yaml` (`default_effort`) |
| `output_config.format`, giới hạn JSON Schema (`additionalProperties: false`, không có `minimum`/`maxLength`..., `minItems` 0 hoặc 1), thứ tự thuộc tính, enum có thể đổi hoa thường, `messages.parse` | [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) | Mục 5, bài 3, `claude_vi.rules.schema_errors` |
| Thinking `enabled` bị bỏ từ 4.7; `between_tools` chỉ có trên Sonnet 5.5; `disabled`/`between_tools` không đi cùng effort `xhigh`/`max` | [Claude API errors](https://platform.claude.com/docs/en/api/errors) | Luật mới trong `claude_vi.rules` |

## Tài nguyên tham khảo thêm (chỉ liên kết)

- [anthropics/prompt-eng-interactive-tutorial](https://github.com/anthropics/prompt-eng-interactive-tutorial): viết cho Claude 3, chưa có giấy phép mở — chỉ đọc, không sao chép.
- [Metaprompt (Claude Cookbook, MIT)](https://colab.research.google.com/github/anthropics/claude-cookbooks/blob/main/misc/metaprompt.ipynb): sinh bản prompt đầu tiên.

## Chi phí ước tính

5 script, 8 lời gọi, mỗi lời gọi tối đa 1.024 token ra với Haiku 5.5 ($0,10 / $0,50 mỗi MTok): trường hợp xấu nhất khoảng 8 × 1.024 × 0,50 / 10⁶ ≈ $0,004, cộng phần input không đáng kể.
