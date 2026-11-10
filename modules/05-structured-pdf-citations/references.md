# Nguồn · Module 05

Kiểm ngày **09/11/2026**. Nội dung bài viết bằng lời của repo.

| Chủ đề | Nguồn | Dùng cho |
|---|---|---|
| `output_config.format`; giới hạn JSON Schema (không `minimum`/`maxLength`/đệ quy, `minItems` 0 hoặc 1, regex không backreference/lookaround/`\b`); thứ tự thuộc tính; refusal, `max_tokens`, enum đổi hoa thường; giới hạn 20 tool strict / 24 optional / 16 union tính gộp; "Schema is too complex for compilation"; cache bản biên dịch 24 giờ; SDK transformation (bỏ ràng buộc, chép vào description, thêm `additionalProperties`); `output_format` bị bỏ | [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) | Mục 1, bài 1, `claude_vi.rules.complexity_errors` và kiểm `pattern` |
| PDF thành ảnh + text từng trang; 1.500–3.000 token text mỗi trang cộng token ảnh; base64 / URL / Files API; 128 MB; 600 trang (100 nếu context dưới 1M); đặt PDF trước text | [PDF support](https://platform.claude.com/docs/en/build-with-claude/pdf-support) | Mục 2, script 02 |
| Cắt theo câu / custom content; bật cho tất cả hoặc không; `title`/`context` không được trích; chỉ số (ký tự từ 0, trang từ 1, block từ 0, end không tính); `cited_text` không tính token; `citations_delta`; không dùng chung với structured outputs; cách "mỗi trường một dòng" và 4 bước tách; tránh prompt "chỉ trả JSON" | [Citations](https://platform.claude.com/docs/en/build-with-claude/citations) | Mục 3–6, bài 2, bài 3, mock custom content và stream citations |
| Giới hạn request 32 → 128 MB | [Release notes 28/10/2026](https://platform.claude.com/docs/en/release-notes/overview) | "Điều gì đã thay đổi" |
| `anthropic.transform_schema`, `messages.parse(output_format=...)` | `anthropic` Python SDK 1.17.0 (đọc mã nguồn đã cài) | Mục 1, script 01, bài 1 |

## Chi phí ước tính

5 script, 5 lời gọi (lời gọi đầu ở script 05 bị chặn ngay tại máy; ở API thật nó cũng trả 400). Output trường hợp xấu nhất với Haiku 5.5: 5 × 1.024 × $0,50/MTok ≈ $0,003. Input: PDF mẫu 2 trang cỡ vài nghìn token text cộng token ảnh, các script khác dưới 1.000 token; tổng input dưới 20.000 token ≈ $0,002. Cả module dưới $0,01. Đây là ước tính, chưa đo bằng API thật.
