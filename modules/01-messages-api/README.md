# 01 · Messages API

**Loại:** Learn + Build · **Thời lượng:** khoảng 2 giờ · **Chi phí:** $0 ở mock mode; dưới $0,01 nếu chạy thật với `claude-haiku-5-5` (giá kiểm 24/10/2026, xem [references.md](references.md))

## Mục tiêu

Sau module này bạn:

- Viết được một request đúng: `model`, `max_tokens`, `system`, `messages`.
- Giữ được hội thoại nhiều lượt mà không làm hỏng block thinking.
- Đọc response đúng cách: `content` blocks, `stop_reason`, `usage`.
- Ước tính được chi phí từ `usage`.
- Stream được câu trả lời và biết khi nào nên stream.
- Phân biệt lỗi phải sửa request (400) với lỗi chỉ cần thử lại (429, 529).

| Learn | Build |
|---|---|
| Đọc mục 1–7 bên dưới, chạy 5 script trong `python/` | Làm 3 bài trong `exercises/`, chấm bằng test |

## Vì sao học cái này trước

Mọi thứ khác — tool use, RAG, agent — đều là các lời gọi Messages API được ghép lại. Hiểu sai một chi tiết ở đây (ví dụ lấy text bằng `content[0]`) thì sẽ hỏng ở mọi module sau.

## Tối thiểu chạy được

```bash
CLAUDE_MOCK=1 uv run python modules/01-messages-api/python/01_hello.py
```

Mock mode không gọi mạng, không cần key. Response giả lập có cùng shape với API thật, kể cả block `thinking` đứng đầu.

| Script | Ý chính |
|---|---|
| [`01_hello.py`](python/01_hello.py) | Lời gọi đầu tiên, đọc block, `stop_reason`, token, chi phí |
| [`02_multi_turn.py`](python/02_multi_turn.py) | Hội thoại nhiều lượt: gửi lại lịch sử |
| [`03_stop_reason_usage.py`](python/03_stop_reason_usage.py) | `max_tokens` quá nhỏ thì sao; token thinking |
| [`04_streaming.py`](python/04_streaming.py) | Stream từng mảnh chữ, rồi lấy Message hoàn chỉnh |
| [`05_errors.py`](python/05_errors.py) | Lỗi 400 chặn tại máy; lỗi 429/529 và retry |

Chạy cả 5: `for f in modules/01-messages-api/python/*.py; do CLAUDE_MOCK=1 uv run python "$f"; done`

## 1. Cấu trúc request

Một request tối thiểu có ba trường bắt buộc:

| Trường | Ý nghĩa | Ghi chú |
|---|---|---|
| `model` | Model nào trả lời | Trong repo này chỉ lấy từ [`config/models.yaml`](../../config/models.yaml) |
| `max_tokens` | Trần số token **output** | Thinking cũng tính vào trần này |
| `messages` | Danh sách lượt `user` / `assistant` | Phải kết thúc bằng lượt `user` trên model 5.x |

Trường tuỳ chọn hay dùng nhất là `system`: chỉ dẫn áp dụng cho cả cuộc hội thoại (vai trò, giọng văn, ràng buộc). Đặt nó ở tham số `system` riêng, không phải một message.

```python
client.create(
    system="Bạn là trợ giảng, trả lời bằng tiếng Việt.",
    messages=[{"role": "user", "content": "Prompt caching là gì?"}],
)
```

`claude_vi` tự điền `model` và `max_tokens` từ `.env` nếu bạn không truyền.

## 2. Hội thoại nhiều lượt

**Vì sao:** API là *stateless* — không lưu gì giữa hai lần gọi. Claude "nhớ" lượt trước chỉ vì bạn gửi lại lượt đó.

**Làm thế nào:** sau mỗi response, nối `{"role": "assistant", "content": msg.content}` vào lịch sử, rồi nối lượt user tiếp theo. Xem [`02_multi_turn.py`](python/02_multi_turn.py).

Hai điều quan trọng trên model 5.x:

- Gửi lại **nguyên vẹn** `msg.content`, kể cả block `thinking` có trường `thinking` rỗng. Đừng lọc chỉ lấy text.
- Lịch sử chỉ **nối thêm** (append-only). Block thinking gắn với phần hội thoại đứng trước nó; sửa `system` hoặc lượt cũ rồi gửi lại block đó có thể bị lỗi 400.

Hệ quả về chi phí: mỗi lượt gửi lại toàn bộ lịch sử, nên `input_tokens` tăng dần theo độ dài hội thoại. Module 06 sẽ dùng prompt caching để giảm chi phí này.

## 3. Đọc response: content blocks

`msg.content` là một **danh sách** block, không phải một chuỗi. Trên model 5.x thinking bật sẵn (adaptive thinking), nên response thường có dạng:

```text
content = [ thinking(thinking="", signature="..."), text(text="Câu trả lời...") ]
```

Text của thinking mặc định bị ẩn (`display: "omitted"`) — block vẫn có mặt, chỉ trường `thinking` rỗng.

Vì vậy **luôn** lấy text bằng `text_of(msg)`: hàm này ghép mọi block `text` và bỏ qua các block khác. Code `content[0]` trong tutorial cũ sẽ lấy nhầm block thinking.

## 4. `stop_reason`

Đọc `stop_reason` **trước** khi tin vào text.

| Giá trị | Nghĩa | Nên làm |
|---|---|---|
| `end_turn` | Trả lời xong tự nhiên | Dùng kết quả |
| `stop_sequence` | Gặp một chuỗi trong `stop_sequences` bạn đặt | Dùng kết quả; xem `msg.stop_sequence` |
| `max_tokens` | Chạm trần `max_tokens` — **bị cắt ngang** | Tăng `max_tokens` hoặc yêu cầu ngắn hơn |
| `model_context_window_exceeded` | Đầy cửa sổ ngữ cảnh | Coi như bị cắt; rút gọn lịch sử |
| `tool_use` | Claude muốn gọi tool | Module 03 |
| `pause_turn` | Vòng lặp server tool chạm giới hạn | Gửi lại nội dung assistant y nguyên để tiếp tục |
| `refusal` | Claude từ chối | Đọc `msg.stop_details`; thử model khác hoặc diễn đạt lại |

[`03_stop_reason_usage.py`](python/03_stop_reason_usage.py) gọi cùng một câu hỏi với `max_tokens=1024` và `max_tokens=10` để bạn thấy `end_turn` và `max_tokens`.

## 5. `usage` và chi phí

`msg.usage` cho biết bạn bị tính bao nhiêu token:

- `input_tokens` — mọi thứ bạn gửi (system + toàn bộ lịch sử).
- `output_tokens` — mọi thứ Claude sinh ra, **gồm cả thinking**, kể cả khi text thinking bị ẩn.
- `output_tokens_details.thinking_tokens` — phần thinking trong `output_tokens` (có thể là `None`).

Chi phí = `input_tokens × giá input + output_tokens × giá output`, giá tính theo triệu token (MTok). `estimate_cost_usd(msg)` làm phép tính này với giá trong `config/models.yaml`.

Ví dụ với Haiku 5.5 ($0,10 / MTok vào, $0,50 / MTok ra): 200 token vào và 1.000 token ra tốn 200 × 0,10/10⁶ + 1.000 × 0,50/10⁶ ≈ **$0,00052**.

`estimate_cost_usd` là ước tính thô. Nó **không** tính: giá cache (module 06), giá cao hơn của Haiku 5.5 khi prompt trên 100.000 token, hệ số `inference_geo`, giá batch. Hoá đơn thật xem ở Console.

## 6. Streaming

**Vì sao:**

- Người dùng thấy chữ ngay thay vì chờ cả câu trả lời.
- Request dài (nhiều phút) dễ bị mạng cắt khi im lặng quá lâu. SDK từ chối request không stream nếu ước tính nó vượt 10 phút.

**Làm thế nào:** dùng `client.stream(...)` như context manager, giống hệt SDK thật:

```python
with client.stream(messages=[{"role": "user", "content": "..."}]) as s:
    for chunk in s.text_stream:
        print(chunk, end="", flush=True)
    msg = s.get_final_message()   # Message hoàn chỉnh, có usage và stop_reason
```

Bên dưới là chuỗi server-sent events: `message_start` → với mỗi block: `content_block_start`, nhiều `content_block_delta`, `content_block_stop` → `message_delta` (có `stop_reason`, `usage`) → `message_stop`. Delta có các loại `text_delta`, `thinking_delta`, `signature_delta`. `text_stream` chỉ lấy `text_delta`.

Lưu ý: `usage` trong `message_delta` là số **cộng dồn**, không phải số tăng thêm.

## 7. Xử lý lỗi

| Mã | Loại | Thử lại? |
|---|---|---|
| 400 | `invalid_request_error` — request sai (hoặc chạm spend limit bạn tự đặt) | Không. Sửa request |
| 401 / 403 | Key sai / không có quyền | Không |
| 404 | Sai đường dẫn hoặc ID | Không |
| 413 | Request quá lớn (Messages API: 32 MB) | Không |
| 429 | `rate_limit_error` — vượt rate limit | Có, theo `retry-after` |
| 429 | `rate_limit_error` với `error.details.error_code = "enforced_spend_limit_reached"` — chạm spend cap của tier | Không: không có `retry-after`, thử lại vẫn lỗi tới đầu tháng sau |
| 500 | `api_error` — lỗi nội bộ | Có, với backoff |
| 504 | `timeout_error` | Dùng streaming cho request dài |
| 529 | `overloaded_error` — API quá tải chung | Có, với backoff |

Ba điều cần nhớ:

1. **SDK đã tự thử lại** lỗi kết nối, 429 và 5xx — 2 lần, exponential backoff, tôn trọng header `retry-after`. Muốn đổi thì dùng `Anthropic(max_retries=...)`. Đừng bọc thêm vòng retry của riêng bạn bên ngoài, sẽ nhân số lần thử lên.
2. Bắt exception có kiểu (`anthropic.RateLimitError`, `anthropic.OverloadedError`, `anthropic.BadRequestError`...), không so chuỗi thông báo.
3. Ghi lại `e.request_id` (hoặc `msg._request_id`) — cần khi hỏi support.

`claude_vi` còn chặn sẵn tại máy các request chắc chắn lỗi 400 trên model 5.x và báo bằng tiếng Việt (`ModelRuleError`), để không tốn một request.

Khi đang stream, lỗi có thể đến **sau** khi đã nhận HTTP 200, dưới dạng event `error`. SDK chuyển nó thành exception khi bạn duyệt stream.

## Bẫy thường gặp

- **Lấy text bằng `content[0]`.** Block đầu thường là thinking. Dùng `text_of(msg)`.
- **Không đọc `stop_reason`.** Câu trả lời bị cắt ở `max_tokens` trông vẫn giống câu trả lời bình thường.
- **`max_tokens` quá nhỏ trên model có thinking.** Thinking ăn hết trần, text còn lại rất ngắn hoặc rỗng.
- **Chỉ gửi lại text của lượt assistant.** Làm mất block thinking; với tool use (module 03) sẽ lỗi 400.
- **Sửa lịch sử cũ giữa chừng** (đổi `system`, xoá lượt). Có thể làm block thinking không còn hợp lệ.
- **Đặt chỉ dẫn hệ thống làm message đầu tiên** thay vì tham số `system`.
- **Tự viết vòng retry chồng lên retry của SDK.**
- **Coi `estimate_cost_usd` là hoá đơn.** Nó bỏ qua cache, giá prompt dài, giá batch.
- **Chép code từ tutorial cũ có `temperature`.** Trả 400 trên model 5.x, và Python SDK ≥1.0 đã bỏ tham số này. Xem [legacy/](../../legacy/README.md).

## Điều gì đã thay đổi ở model 5.x

| Trước đây | Bây giờ |
|---|---|
| Response chỉ có block `text` | Thinking bật sẵn; block `thinking` thường đứng đầu, text ẩn mặc định |
| `temperature`, `top_p`, `top_k` để điều khiển | Trả 400; bị bỏ khỏi Python SDK ≥1.0. Điều khiển bằng prompt và `output_config.effort` |
| Prefill: kết thúc `messages` bằng lượt assistant để ép định dạng | Trả 400. Dùng structured outputs (module 05) |
| `thinking={"type": "enabled", "budget_tokens": N}` | Bị bỏ; dùng adaptive thinking + effort (module 07) |
| Tắt thinking bằng `{"type": "disabled"}` | Trong các model repo dùng, chỉ Haiku 5.5 còn nhận (ở effort `high` trở xuống). Sonnet 5.5 dùng `{"type": "between_tools"}`. Opus 5.5 và Fable 5.1 không tắt được |
| Thinking không ràng buộc với lịch sử | Block thinking gắn với phần hội thoại trước nó; giữ lịch sử append-only |
| Chỉ có `system` ở đầu | Có thể chèn message `role: "system"` giữa hội thoại (sau một lượt user) — xem references |

## Bài tập

Ba bài trong [`exercises/`](exercises/), lời giải trong [`solutions/`](solutions/). Mỗi bài là một file có `raise NotImplementedError`; bạn điền code rồi chấm:

```bash
CHAM=exercises uv run pytest modules/01-messages-api -q
```

| Bài | Nội dung |
|---|---|
| [`bai1_hoi_thoai.py`](exercises/bai1_hoi_thoai.py) | Lớp `HoiThoai` giữ lịch sử append-only, giữ nguyên block thinking |
| [`bai2_stop_reason.py`](exercises/bai2_stop_reason.py) | Chọn hành động theo `stop_reason`; cộng token và chi phí cả hội thoại |
| [`bai3_retry.py`](exercises/bai3_retry.py) | Exponential backoff có jitter và `retry-after`; không thử lại lỗi 400 |

Test chạy ở mock mode, không cần key. Lỗi 429/529 được giả lập bằng `MockAnthropic(errors=[529, 429])`.

Tự kiểm tra lý thuyết: [quiz.md](quiz.md). Nguồn và ngày kiểm: [references.md](references.md).

## Tiếp theo

Module 02 — Prompt engineering: viết `system` và prompt để có câu trả lời ổn định mà không cần `temperature`.
