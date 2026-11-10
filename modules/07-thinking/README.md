# 07 · Thinking

**Loại:** Learn + Build · **Thời lượng:** khoảng 2 giờ · **Cần:** module 01–03 · **Chi phí:** $0 ở mock mode; dưới $0,01 nếu chạy thật với `claude-haiku-5-5` (giá kiểm 24/10/2026, xem [references.md](references.md))

## Mục tiêu

Sau module này bạn:

- Hiểu thinking là gì, được tính tiền thế nào, và vì sao block `thinking` thường rỗng.
- Đọc được tóm tắt thinking bằng `display: "summarized"` và biết nó **không** phải suy nghĩ gốc.
- Giảm hoặc tắt thinking đúng luật của từng model.
- Chọn giữa `effort` và `max_tokens` khi muốn kiểm soát chi phí.
- Xử lý `redacted_thinking`, stream thinking, và thinking trong vòng lặp tool.
- Giữ lịch sử append-only để block thinking không bị prefix check từ chối.

| Learn | Build |
|---|---|
| Đọc mục 1–7, chạy 5 script trong `python/` | Làm 3 bài trong `exercises/`, chấm bằng test |

## Vì sao học cái này

Model trả lời một lượt phải làm đúng ngay từ lần đầu: không nháp, không kiểm lại, không đổi hướng giữa chừng. Với bài toán nhiều bước (chứng minh, sửa lỗi khó, agent chạy lâu), cách làm đầu tiên thường chưa tốt. Thinking cho Claude chỗ để nháp: đọc lại câu hỏi, thử hướng, kiểm kết quả trung gian, bỏ hướng sai, rồi mới trả lời.

Trên model 5.x thinking **bật sẵn**. Bạn không chọn có dùng nó hay không; bạn chọn dùng bao nhiêu, và phải viết code không làm hỏng nó. Ba module trước đã chạm vào thinking (`text_of`, giữ block trong tool loop). Module này gom lại thành quy tắc đầy đủ.

## Tối thiểu chạy được

```bash
CLAUDE_MOCK=1 uv run python modules/07-thinking/python/01_doc_thinking.py
```

| Script | Ý chính |
|---|---|
| [`01_doc_thinking.py`](python/01_doc_thinking.py) | `display` "omitted" và "summarized"; token bị tính không đổi |
| [`02_tat_thinking.py`](python/02_tat_thinking.py) | Bảng luật tắt/giảm thinking của từng model (kiểm tại máy) |
| [`03_max_tokens.py`](python/03_max_tokens.py) | Thinking ăn vào `max_tokens`; text bị cắt hoặc rỗng |
| [`04_stream_thinking.py`](python/04_stream_thinking.py) | `thinking_delta`, `signature_delta`, ghép bằng `get_final_message()` |
| [`05_append_only.py`](python/05_append_only.py) | Sửa `system` giữa chừng → 400; thêm chỉ dẫn bằng message `system` |

Mock mô phỏng: số token thinking theo effort, text tóm tắt khi `summarized`, chữ ký riêng cho từng block, `redacted_thinking` (bật bằng `MockAnthropic(redacted=True)`), lỗi 400 khi sửa block thinking trong tool loop, và prefix check.

## 1. Thinking hoạt động thế nào

Khi thinking bật, response có một hoặc nhiều block `thinking` **trước** các block `text`:

```text
content = [ thinking(thinking="", signature="EqQB..."), text(text="Đáp án...") ]
```

- **`signature`**: bản mã hoá của toàn bộ suy nghĩ. Bạn không đọc được nó, chỉ gửi lại nguyên vẹn. API giải mã để Claude tiếp tục từ chỗ đã nghĩ.
- **`thinking`**: text hiển thị. Mặc định rỗng trên model 5.x.
- **Chi phí**: token thinking tính là **output token**, kể cả khi bạn không thấy chữ nào, và cùng tính vào `max_tokens` với text.

Chế độ trên model 5.x là **adaptive thinking**: Claude tự quyết có nghĩ không và nghĩ sâu bao nhiêu, dựa vào độ khó và `effort`. Câu hỏi dễ có thể không có block thinking nào. Đừng viết code giả định block đầu luôn là thinking; đó là lý do dùng `text_of(msg)` và lọc block theo `type`.

## 2. Đọc thinking: `display`

| `display` | Block `thinking` chứa gì | Mặc định trên |
|---|---|---|
| `"omitted"` | Trường `thinking` rỗng, chỉ có `signature` | Mọi model 5.x trong repo |
| `"summarized"` | Một bản tóm tắt dễ đọc | Opus 4.6, Sonnet 4.6 và cũ hơn |
| `"updates"` (beta) | Chỉ các ghi chú tiến độ giữa các lần gọi tool có chữ | Cần beta header; `claude_vi` không hỗ trợ |

```python
client.create(messages=[...], thinking={"type": "adaptive", "display": "summarized"})
```

Ba điều cần biết về `"summarized"`:

1. **Đó là tóm tắt, không phải suy nghĩ gốc.** Một model khác viết bản tóm tắt. Không có cài đặt nào trả về chuỗi suy nghĩ gốc.
2. **Tiền không đổi.** Bạn trả cho toàn bộ token thinking gốc, không phải số token của bản tóm tắt. Số token bạn thấy không khớp `output_tokens`.
3. **Muốn xem lý luận thì đọc block thinking**, đừng xin "giải thích từng bước suy nghĩ" trong câu trả lời. Trên Fable 5.x, Opus 5.5, Sonnet 5.5, yêu cầu kiểu đó có thể bị từ chối với `stop_details.category: "reasoning_extraction"`.

`"omitted"` không rẻ hơn. Lợi ích của nó là tốc độ: khi stream, server bỏ qua phần chữ thinking nên chữ của câu trả lời tới sớm hơn.

### `redacted_thinking`

Đôi khi một phần suy nghĩ bị che vì lý do an toàn. API trả về block `redacted_thinking` với trường `data` mã hoá, không có chữ. Gửi nó lại nguyên vẹn như block thinking. Bẫy hay gặp: code lọc `b.type == "thinking"` khi gửi lại sẽ làm rơi block này, và vòng tool lỗi 400.

## 3. Giảm hoặc tắt thinking

Không có lệnh tắt chung. Mỗi model một luật (docs Thinking, kiểm 09/11/2026):

| Model | `"disabled"` | `"between_tools"` | Cách giảm thinking |
|---|---|---|---|
| Haiku 5.5 | Được, ở effort `high` trở xuống | 400 | `disabled`, hoặc effort thấp |
| Sonnet 5.5 | 400 | Được, ở effort `high` trở xuống | `between_tools` tắt phần nghĩ đầu lượt |
| Opus 5.5 | 400 | 400 | Chỉ effort |
| Fable 5.1, Fable 5.2 | 400 | 400 | Chỉ effort |

Mọi model 5.x: `thinking: {"type": "enabled", "budget_tokens": N}` (extended thinking kiểu cũ) trả 400.

Chi tiết dễ sai:

- `disabled` hoặc `between_tools` đi cùng effort `xhigh`/`max` → 400. Muốn ít thinking thì hạ effort trước.
- `display` không đi cùng `disabled`. `between_tools` không nhận trường nào khác.
- `between_tools` trên Sonnet 5.5 vẫn trả các ghi chú tiến độ (có chữ) giữa các lần gọi tool.
- Haiku 5.5 tắt thinking mà lại xin JSON: model có thể bỏ qua một lần gọi tool cần thiết.

Đừng chép luật này vào code. Đọc từ `config/models.yaml` (bài 1), hoặc từ Models API (`capabilities.thinking.types.disabled.supported`, `scripts/model_sync.py`). Khi có model mới, chỉ YAML đổi.

[`02_tat_thinking.py`](python/02_tat_thinking.py) in bảng trên bằng cách cho `claude_vi` kiểm từng tổ hợp tại máy, không gửi request nào.

## 4. Effort, `max_tokens` và chi phí

Hai núm vặn, hai việc khác nhau:

| | `output_config.effort` | `max_tokens` |
|---|---|---|
| Loại | Tín hiệu hành vi, **mềm** | Trần **cứng** |
| Tác động | Mọi token output: thinking, độ dài text, số lần gọi tool | Tổng thinking + text của lượt này |
| Khi nào dùng | Muốn rẻ/nhanh hơn trên cả loạt request | Muốn chắc chắn không vượt một mức chi |

Mặc định: `medium` trên Haiku 5.5 và Opus 5.5; `high` trên Sonnet 5.5, Fable 5.1, Fable 5.2. Đặt effort bằng mặc định cho kết quả y như không đặt.

Thứ tự gỡ rối khi chi phí cao hoặc câu trả lời bị cắt:

1. `stop_reason == "max_tokens"` và text rỗng → thinking đã dùng hết trần. **Tăng `max_tokens`.** Bạn đã trả tiền cho phần thinking đó mà không nhận được câu trả lời.
2. Chi phí cao trên cả loạt request → **hạ effort**. Nó thu nhỏ cả response, thinking cũng giảm theo.
3. Claude nghĩ quá ít trên bài khó → nâng effort.
4. Cần thinking tắt hẳn → `disabled` hoặc `between_tools`, chỉ trên model cho phép.

Docs khuyên: đặt effort tường minh, đo trên bài toán của chính bạn trước khi đổi mức, và khi dùng `high` trở lên thì cho `max_tokens` rộng. `max_tokens` trên 21.333 thì Python SDK bắt dùng streaming (kiểm tra phía client để tránh timeout HTTP).

Trong một hội thoại dùng prompt caching, đổi effort hoặc cấu hình thinking giữa các request làm mất cache (module 06). Effort theo từng message (giữ được cache) đang beta, `claude_vi` chưa hỗ trợ.

## 5. Thinking trong vòng lặp tool

Module 03 đã dạy: gửi lại block thinking **nguyên vẹn** cùng `tool_use`. Lý do: với Claude, cả vòng tool là **một lượt assistant**. Khi nhận `tool_result`, Claude tiếp tục đúng câu trả lời đang dở, nên cần suy nghĩ trước đó.

Quy tắc từ docs:

- **Bắt buộc:** trong một lượt có tool, gửi lại mọi block `thinking` và `redacted_thinking`, đúng thứ tự, không sửa, không bỏ bớt.
- **Nên:** giữa các lượt, gửi lại tất cả. API tự lọc và chỉ tính tiền block thật sự đưa vào context.
- **Được phép:** ngoài tool use, bỏ thinking của các lượt cũ.
- **Không đổi cấu hình thinking giữa một lượt** (giữa `tool_use` và `tool_result`). API không báo lỗi mà lặng lẽ tắt thinking cho request đó. Đổi giữa các lượt thì được.

Với adaptive thinking (mọi model 5.x trong repo), Claude có thể suy nghĩ **giữa** các lần gọi tool (interleaved thinking), không cần beta header, nên block thinking có thể xuất hiện ở nhiều chỗ trong một lượt. Fable 5.x, Opus 5.5 và Sonnet 5.5 còn có thể viết một ghi chú tiến độ ngắn trước mỗi lần gọi tool, dưới dạng một block thinking riêng.

Trên Haiku 5.5, Sonnet 5.5, Opus 5.5 và Fable 5.x, block thinking của các lượt trước được **giữ lại** trong context. Chúng tính là input token như phần lịch sử còn lại. Hội thoại dài sẽ tích luỹ thinking; đếm token (module 06) cho đúng.

## 6. Stream thinking

Block thinking stream bằng các `thinking_delta`, rồi đúng một `signature_delta` ngay trước `content_block_stop`. Sau đó mới tới text. Với `"omitted"`, mỗi block thinking chỉ có một `thinking_delta` rỗng rồi chữ ký.

Đừng tự nối delta để dựng lại block. Dùng `s.get_final_message()`: nó ghép thinking và chữ ký đúng cách, và kết quả gửi lại được ngay. Xem [`04_stream_thinking.py`](python/04_stream_thinking.py).

## 7. Lịch sử append-only và prefix check

Đây là thay đổi dễ làm hỏng code cũ nhất.

Trên Haiku 5.5, Sonnet 5.5, Opus 5.5, Fable 5.1 và Fable 5.2, một block thinking chỉ hợp lệ khi **mọi thứ gửi trước nó không đổi** ở các request sau. API gọi đây là *prefix check*. Phần được kiểm gồm ba thứ:

- tham số `system`;
- danh sách `tools`;
- mọi message đứng trước block đó.

`effort`, `max_tokens`, `output_config`, `tool_choice` không thuộc phần được kiểm. Các block thinking cũ hơn cũng không: bỏ các block cũ nhất (từ đầu lịch sử) được phép, bỏ một block ở giữa thì các block sau nó hỏng.

Khi kiểm không qua: tài khoản tạo từ 31/8/2026 nhận lỗi 400 (`Invalid signature in thinking block. The block is bound to a different conversation...`) trên mọi model kể trên. Tài khoản cũ hơn chỉ bị 400 trên Fable 5.2 (và Mythos 5.1/5.2); trên các model còn lại block lệch vẫn tới model mà không báo lỗi. Vì vậy **chạy không lỗi trên key của bạn không chứng minh code đúng**: người dùng code của bạn bằng tài khoản mới sẽ bị 400. Mock của repo luôn hành xử như tài khoản mới.

Những việc làm hỏng prefix, và cách thay:

| Code của bạn... | Thay bằng |
|---|---|
| Dựng lại `system` mỗi lượt (chèn ngày giờ, cờ chế độ) | Giữ `system` cố định; thêm một message `{"role": "system", ...}` mới |
| Dựng lại ngữ cảnh trong lượt user đầu tiên | Dựng một lần, gửi lại y nguyên; phần thay đổi đặt ở lượt mới nhất |
| Rút gọn kết quả tool cũ | Rút gọn **trước** khi gửi lần đầu |
| Thêm/bớt tool giữa chừng | Mid-conversation tool changes (beta, chưa có trong `claude_vi`) |
| Dựng lại phiên đã lưu từ template | Lưu đúng những gì đã gửi và nhận, rồi phát lại |
| Lọc bỏ vài block thinking ở giữa | Gửi lại lượt assistant đúng như đã nhận |

### Message `system` giữa hội thoại

Thay vì sửa tham số `system`, nối thêm một message có `role: "system"` tại chỗ chỉ dẫn bắt đầu có hiệu lực. Prefix giữ nguyên, prompt cache cũng giữ nguyên. Không cần beta header trên các model 5.x trong repo.

```python
messages = [u1, a1, u2, {"role": "system", "content": "Từ giờ trả lời bằng tiếng Anh."}]
```

Luật vị trí (sai là 400, `claude_vi` chặn trước):

- Không được là message đầu tiên. Chỉ dẫn từ đầu thì dùng tham số `system`.
- Phải đứng **ngay sau một lượt user** (kể cả lượt chỉ có `tool_result`), và **trước một lượt assistant** hoặc ở cuối danh sách.
- Không được chen giữa `tool_use` và `tool_result` của nó.

Không đặt dữ liệu từ bên ngoài (kết quả tool, tài liệu, nội dung web) vào message `system`: Claude coi đó là chỉ dẫn của nhà phát triển và làm theo. Dữ liệu ngoài vẫn để trong `tool_result`.

## Bẫy thường gặp

- **Lấy text bằng `content[0]`.** Block đầu thường là thinking, hoặc không có thinking nào. Dùng `text_of(msg)`.
- **Nghĩ `"omitted"` rẻ hơn.** Chỉ nhanh hơn; tiền như nhau.
- **Coi tóm tắt thinking là suy nghĩ gốc**, hoặc đếm token của nó để ước chi phí.
- **Xin "giải thích từng bước suy nghĩ" trong câu trả lời** → có thể bị từ chối `reasoning_extraction`. Đọc block thinking.
- **Gửi `"disabled"` cho Opus/Sonnet/Fable**, hoặc `disabled` + effort `xhigh`.
- **Truyền `"adaptive"` làm giá trị effort.** `adaptive` là chế độ thinking.
- **`max_tokens` quá sát** → `stop_reason: "max_tokens"`, text rỗng, vẫn mất tiền thinking.
- **Lọc `type == "thinking"` khi gửi lại** → rơi `redacted_thinking`, vòng tool lỗi 400.
- **Sửa text của block thinking đã tóm tắt** trước khi gửi lại → 400.
- **Đổi cấu hình thinking giữa `tool_use` và `tool_result`** → thinking bị tắt lặng lẽ.
- **Chèn ngày giờ vào `system` mỗi lượt** → prefix check 400 trên tài khoản mới.
- **Tin rằng code đúng vì key của mình không lỗi.** Tài khoản cũ được nới lỏng.

## Điều gì đã thay đổi ở model 5.x

| Trước đây | Bây giờ |
|---|---|
| Thinking tắt mặc định, bật bằng `{"type": "enabled", "budget_tokens": N}` | Adaptive thinking bật sẵn; `budget_tokens` trả 400; điều khiển bằng `effort` |
| Thinking trả về dạng tóm tắt (`display` mặc định `"summarized"`) | Mặc định `"omitted"`: block có mặt nhưng trường `thinking` rỗng |
| Tắt bằng `{"type": "disabled"}` trên mọi model | Chỉ Haiku 5.5 (effort ≤ `high`); Sonnet 5.5 dùng `between_tools`; Opus 5.5, Fable 5.x không tắt được |
| Interleaved thinking cần beta header | Tự động với adaptive thinking |
| Thinking của lượt cũ bị bỏ khỏi context | Haiku/Sonnet/Opus 5.5 và Fable 5.x giữ lại, tính là input token |
| Sửa `system` giữa hội thoại là chuyện bình thường | Làm hỏng block thinking (prefix check); dùng message `system` giữa hội thoại |
| Thinking dùng được ở mọi tài khoản | Block của Sonnet 5.5, Haiku 5.5, Fable 5.2 chỉ dùng được trong tài khoản đã tạo ra nó |

## Bài tập

```bash
CHAM=exercises uv run pytest modules/07-thinking -q
```

| Bài | Nội dung |
|---|---|
| [`bai1_cau_hinh.py`](exercises/bai1_cau_hinh.py) | Chọn cấu hình ít thinking nhất / xem tóm tắt, đọc luật từ `config/models.yaml` |
| [`bai2_bao_cao.py`](exercises/bai2_bao_cao.py) | Đếm block, tóm tắt, tỉ lệ token thinking; chẩn đoán `stop_reason` |
| [`bai3_append_only.py`](exercises/bai3_append_only.py) | Hội thoại append-only: chỉ dẫn mới bằng message `system`, lưu và phát lại phiên |

Lời giải trong [`solutions/`](solutions/). Tự kiểm tra: [quiz.md](quiz.md). Nguồn: [references.md](references.md).

## Tiếp theo

Module 06 — Chi phí: prompt caching, đếm token, Batch API, message threads.
