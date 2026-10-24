# 03 · Tool use

**Loại:** Learn + Build · **Thời lượng:** khoảng 3 giờ · **Chi phí:** $0 ở mock mode; dưới $0,01 nếu chạy thật với `claude-haiku-5-5` (giá kiểm 24/10/2026, xem [references.md](references.md))

## Mục tiêu

Sau module này bạn:

- Định nghĩa được tool với mô tả tốt và schema strict.
- Viết được một vòng tool use bằng tay: `tool_use` → chạy hàm → `tool_result`.
- Viết được vòng lặp nhiều lượt, xử lý nhiều tool gọi song song.
- Trả lỗi của tool về cho Claude bằng `is_error`.
- Giải thích được vì sao phải gửi lại block thinking nguyên vẹn trong vòng lặp tool.

| Learn | Build |
|---|---|
| Đọc mục 1–6, chạy 5 script trong `python/` | Làm 3 bài trong `exercises/`, chấm bằng test |

## Vì sao học cái này

Claude chỉ sinh ra chữ. **Tool use** (còn gọi là function calling — gọi hàm) cho phép Claude yêu cầu code của bạn làm việc thay nó: tra cơ sở dữ liệu, gọi API, tính toán. Đây là nền móng của mọi agent (module 08–10).

Điểm mấu chốt: **Claude không tự chạy code của bạn.** Nó trả về một yêu cầu có cấu trúc; code của bạn quyết định có chạy hay không, rồi gửi kết quả lại.

## Tối thiểu chạy được

```bash
CLAUDE_MOCK=1 uv run python modules/03-tool-use/python/01_mot_tool.py
```

| Script | Ý chính |
|---|---|
| [`tools_mau.py`](python/tools_mau.py) | Hai tool mẫu (AQI, nhiệt độ) với dữ liệu bịa, dùng chung |
| [`01_mot_tool.py`](python/01_mot_tool.py) | Một vòng tool use viết tay từng bước |
| [`02_vong_lap.py`](python/02_vong_lap.py) | Vòng lặp nhiều lượt, nhiều tool gọi song song |
| [`03_tool_choice.py`](python/03_tool_choice.py) | `auto`, `auto` + `disable_parallel_tool_use`, `none` |
| [`04_loi_tool.py`](python/04_loi_tool.py) | Tool lỗi → `is_error` với lời nhắn có ích |
| [`05_giu_thinking.py`](python/05_giu_thinking.py) | Lọc bỏ thinking → 400; gửi nguyên vẹn → chạy |

Ở mock mode: khi có `tools`, lượt đầu mock gọi **mọi** tool một lần (song song), với đầu vào là giá trị hợp lệ đầu tiên theo schema (ví dụ phần tử đầu của `enum`). Khi nhận `tool_result`, mock trả lời bằng cách nhắc lại kết quả.

## 1. Một vòng tool use

```text
bạn  ── messages + tools ─────────────▶ Claude
bạn  ◀── stop_reason="tool_use", block tool_use {id, name, input}
bạn: chạy hàm name(**input)
bạn  ── + lượt assistant (msg.content nguyên vẹn)
        + lượt user [tool_result {tool_use_id, content}] ──▶ Claude
bạn  ◀── stop_reason="end_turn", câu trả lời
```

Ba trường của block `tool_use`: `id` (để ghép kết quả), `name`, `input` (theo `input_schema`). Block `tool_result` có `tool_use_id`, `content` (chuỗi hoặc danh sách block), và `is_error` (tuỳ chọn).

## 2. Định nghĩa tool tốt

Một tool gồm `name`, `description`, `input_schema`; tuỳ chọn có `strict`, `input_examples`.

- **`name`** phải khớp `^[a-zA-Z0-9_-]{1,128}$`: không dấu tiếng Việt, không khoảng trắng. Khi có nhiều dịch vụ, nên thêm tiền tố (`moi_truong_tra_aqi`, `github_list_prs`).
- **`description` là yếu tố quan trọng nhất** với chất lượng tool use, theo docs. Viết ít nhất 3–4 câu: tool làm gì, khi nào nên (và không nên) dùng, từng tham số nghĩa là gì, tool **không** trả về gì.
- **Gộp các thao tác liên quan** thành ít tool hơn (một tool có tham số `action` thay vì `tao_x`, `sua_x`, `xoa_x`).
- **Trả về ít mà chất**: chỉ những trường Claude cần cho bước tiếp theo.

### Strict tool use

Thêm `"strict": true` để API **đảm bảo** `input` luôn khớp schema (đúng kiểu, đủ trường bắt buộc, `name` luôn hợp lệ). Schema strict tuân theo cùng giới hạn với structured outputs (module 02): `additionalProperties: false`, không có `minimum`/`maxLength`... Tối đa 20 tool strict trong một request.

## 3. Vòng lặp tool

Một câu hỏi có thể cần nhiều lượt gọi tool. Lặp cho tới khi `stop_reason != "tool_use"`:

1. Gửi `messages` + `tools`.
2. `stop_reason == "tool_use"`: nối lượt assistant (**`msg.content` nguyên vẹn**), chạy **mọi** block `tool_use`, gửi **mọi** `tool_result` trong **một** lượt user.
3. Lặp lại. **Luôn đặt giới hạn số lượt** để agent không lặp vô hạn và tốn tiền.

Luật định dạng (sai thì 400 — `claude_vi` chặn trước):

- `tool_result` phải nằm trong lượt user **ngay sau** lượt assistant có `tool_use`.
- Mỗi `tool_use` phải có một `tool_result` tương ứng.
- Trong lượt user đó, các block `tool_result` phải đứng **đầu**; text (nếu có) đặt sau.

Python SDK có **tool runner** tự làm vòng lặp này. Repo dạy cách viết tay trước để bạn hiểu cái mà tool runner che đi.

## 4. Gửi lại thinking nguyên vẹn

Trên model 5.x, lượt assistant có `tool_use` thường có block `thinking` đứng trước (thường với trường `thinking` rỗng, vì text bị ẩn). Khi gửi lại trong vòng lặp:

- **Gửi `msg.content` y nguyên.** Không lọc theo kiểu, không sắp xếp lại, không dựng lại block.
- Nếu bạn lọc block theo kiểu, phải giữ cả `thinking` lẫn `redacted_thinking`.
- Sửa block thinking ở lượt assistant mới nhất → 400 *"thinking blocks ... cannot be modified"*.
- Block thinking còn gắn với phần hội thoại trước nó: đổi `system`, `tools` hay lượt cũ rồi gửi lại có thể bị 400. Giữ lịch sử append-only.

[`05_giu_thinking.py`](python/05_giu_thinking.py) cho thấy cả hai trường hợp. Mock của repo trả đúng lỗi 400 này, nên bài 3 sẽ đỏ nếu bạn làm sai.

## 5. `tool_choice`

| Giá trị | Ý nghĩa | Trong repo |
|---|---|---|
| `{"type": "auto"}` | Claude tự quyết có gọi tool không (mặc định khi có `tools`) | ✅ |
| `{"type": "auto", "disable_parallel_tool_use": true}` | Tối đa một tool mỗi lượt | ✅ |
| `{"type": "none"}` | Không gọi tool | ✅ |
| `any` / `tool` (ép gọi tool) | **400** trên Opus 5.5, Sonnet 5.5, Fable 5.1. Haiku 5.5 nhận, nhưng khi đó bỏ qua thinking | ❌ không dùng |

Muốn Claude dùng tool nhiều hơn thì nói trong prompt: *"Dùng tool để kiểm tra trước khi trả lời."* Muốn đầu vào tool luôn đúng schema thì dùng `strict: true`. Muốn **câu trả lời** có định dạng cố định thì dùng structured outputs.

## 6. Khi tool lỗi, và nội dung không đáng tin

- Tool ném exception → **đừng** để vòng lặp sập, cũng đừng giấu lỗi. Gửi `tool_result` với `"is_error": true` và lời nhắn có ích: chuyện gì xảy ra, nên làm gì tiếp ("Rate limit, thử lại sau 60 giây"), thay vì chỉ "failed".
- Claude gọi tên tool không tồn tại → trả `is_error` kèm danh sách tool hiện có.
- **Kết quả tool là dữ liệu không đáng tin** (trang web, email, file người dùng tải lên): nó có thể chứa chỉ dẫn độc hại (indirect prompt injection — chèn lệnh gián tiếp). Giữ nội dung đó **trong `tool_result`**; đừng chép vào `system` hay vào block text của user.

Chi phí: định nghĩa tool, block `tool_use` và `tool_result` đều tính token. Ngoài ra, khi có `tools`, API tự thêm một system prompt cho tool: 286 token với `auto`/`none` trên Haiku 5.5, Sonnet 5.5 và Opus 5.5.

## Bẫy thường gặp

- **Lọc bỏ block thinking** khi gửi lại lượt assistant → 400.
- **Gửi mỗi `tool_result` trong một lượt user riêng** khi Claude gọi song song nhiều tool. Phải gộp vào một lượt.
- **Đặt text trước `tool_result`** trong lượt user.
- **Quên một `tool_use`** (chỉ chạy tool đầu tiên).
- **Vòng lặp không giới hạn số lượt.**
- **Mô tả tool một dòng.** Claude chọn sai tool hoặc điền sai tham số.
- **Tên tool có dấu hoặc khoảng trắng.**
- **Dùng `tool_choice` any/tool** cho "chắc ăn" → 400 trên hầu hết model 5.x.
- **Để exception của tool làm sập vòng lặp**, hoặc trả `"failed"` không kèm lý do.
- **Tin nội dung trong kết quả tool như chỉ dẫn.**

## Điều gì đã thay đổi ở model 5.x

| Trước đây | Bây giờ |
|---|---|
| `tool_choice={"type": "any"}` để ép gọi tool | 400 trên Opus 5.5, Sonnet 5.5, Fable 5.1. Dùng `auto` + `strict: true` + chỉ dẫn trong prompt |
| Tự validate rồi retry khi input tool sai kiểu | `strict: true` đảm bảo input đúng schema |
| Lượt assistant chỉ có text + tool_use | Thường có block `thinking` đứng trước; phải gửi lại nguyên vẹn |
| Sửa lịch sử thoải mái giữa các lượt | Block thinking gắn với phần trước nó; giữ lịch sử append-only |
| Tool system prompt khoảng 500 token (Sonnet/Haiku 4.5) | 286 token trên Haiku 5.5, Sonnet 5.5, Opus 5.5 |

## Bài tập

```bash
CHAM=exercises uv run pytest modules/03-tool-use -q
```

| Bài | Nội dung |
|---|---|
| [`bai1_dinh_nghia_tool.py`](exercises/bai1_dinh_nghia_tool.py) | Tạo tool strict; kiểm tên, độ dài mô tả, trường bắt buộc |
| [`bai2_chay_tool.py`](exercises/bai2_chay_tool.py) | `tool_use` → `tool_result`; tool không tồn tại và exception → `is_error` |
| [`bai3_vong_lap.py`](exercises/bai3_vong_lap.py) | Vòng lặp hoàn chỉnh: song song, giữ thinking, giới hạn lượt |

Lời giải trong [`solutions/`](solutions/). Tự kiểm tra: [quiz.md](quiz.md). Nguồn: [references.md](references.md).

## Tiếp theo

Capstone c2 — trích xuất dữ liệu thí nghiệm từ PDF: kết hợp citations (module 05) và structured outputs (module 02) trong một pipeline nhiều bước.
