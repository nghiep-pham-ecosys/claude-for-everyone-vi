# Kiểm chứng báo cáo tư vấn (21/10/2026)

Đối chiếu các dữ kiện "chưa xác minh" trong báo cáo ngày 16/10/2026 với nguồn gốc.

| Dữ kiện trong báo cáo | Kết quả | Nguồn |
|---|---|---|
| `anthropics/courses` dùng giấy phép chưa rõ | **Sai một nửa: đã rõ.** File LICENSE ở gốc là **CC BY-NC 4.0** (phi thương mại). Được phép dịch/chuyển thể cho mục đích phi thương mại nếu ghi công và đánh dấu thay đổi — nhưng phần chuyển thể đó **không thể** nằm dưới CC BY 4.0 của repo. | github.com/anthropics/courses/blob/master/LICENSE |
| `anthropics/courses` có thể đã archived 15/9/2026 | **Đúng.** GitHub ghi archived ngày 15/9/2026, chỉ đọc. | github.com/anthropics/courses |
| `prompt-eng-interactive-tutorial` không có LICENSE ở gốc | **Đúng.** Không có file LICENSE ở gốc, repo chưa archive. Không có giấy phép = mặc định không được tái sử dụng. | github.com/anthropics/prompt-eng-interactive-tutorial |
| Claude 3 Haiku retired 20/4/2026 | **Đúng** (nay xác nhận từ nguồn chính thức). | Release notes 20/4/2026 |
| `anthropic>=1.0` bỏ `temperature/top_p/top_k` (nguồn: fork cộng đồng) | **Đúng, và nguồn chính thức.** Python SDK v1.0 (20/8/2026) bỏ ba tham số này, chuyển `httpx` → `httpx2`, yêu cầu Python ≥3.10. Đã kiểm trên SDK 1.17.0: `Messages.create` không còn các tham số này. | Release notes 20/8/2026; `inspect.signature` trên anthropic 1.17.0 |
| Python SDK 1.10.0 (30/9) | **Cũ.** PyPI hiện có **1.17.0**. Ghim theo khoảng `>=1.17,<2`, không ghim cứng một bản. | pypi.org |
| Chỉ Opus 5.5 cấm `tool_choice` any/tool | **Thiếu.** Cũng cấm trên **Fable 5.1** (1/9) và **Sonnet 5.5** (28/9). Haiku 5.5: release notes không nhắc — cần live-smoke. | Release notes 1/9, 22/9, 28/9/2026 |
| Thinking không tắt được trên Opus 5.5 | **Đúng, và thiếu Sonnet 5.5:** Sonnet 5.5 cũng không nhận `"disabled"`; thay bằng `{"type": "between_tools"}` (tắt thinking đầu turn). | Release notes 28/9, Models overview |
| Tokenizer mới tốn "1,0–1,35×" | **Nên ghi "khoảng 30%, tuỳ nội dung"** — đây là con số release notes chính thức dùng (Fable 5, Sonnet 5). | Release notes 9/6, 30/6/2026 |
| Spec MCP hiện hành 2026-07-28 | **Đúng.** Thêm chi tiết: version khai báo theo từng request qua `_meta`, có RPC `server/discover`; bản ≤2025-11-25 dùng handshake. | modelcontextprotocol.io versioning |
| Số khoá Anthropic Academy (13/14/18/27) | **Chưa xác minh.** Không đưa con số vào README; chỉ liên kết trang khoá học. | — |

## Điểm mới phát hiện, báo cáo gốc chưa có

1. **Response có thể bắt đầu bằng block `thinking`** (Haiku 5.5, 7/10/2026): adaptive thinking bật mặc định, text của thinking bị ẩn trừ khi đặt `thinking.display: "summarized"`. Code kiểu `msg.content[0].text` — xuất hiện trong gần như mọi tutorial cũ — **sẽ hỏng**. Wrapper `claude_vi.text_of()` và `check_legacy_params.py` xử lý điểm này.
2. **Thinking block gắn với tài khoản và lịch sử hội thoại** (Sonnet 5.5, Fable 5.1): gửi lại thinking block sau khi đổi `system`/`tools`/turn trước có thể lỗi 400. Ảnh hưởng tới bài "tool loop tự viết" ở module 03 và 08.
3. **Refusal `bio` lại bị tính phí từ 24/9/2026.** Củng cố khuyến nghị: capstone hoá học không đụng tổng hợp chất.

## Hệ quả cho repo

- Nội dung chuyển thể từ `anthropics/courses` (nếu có) phải đặt ở thư mục riêng, gắn **CC BY-NC 4.0** và ghi công. Khuyến nghị vẫn là **không** chuyển thể — tự viết.
- Mock mode phải mô phỏng cả block thinking và luật 400 của từng model, nếu không CI sẽ xanh giả. Đã làm trong `shared/py/claude_vi`.
- Bảng luật trong `config/models.yaml` cần `model-sync` đọc `capabilities.thinking.types.disabled` từ Models API để tự cập nhật thay vì sửa tay.
