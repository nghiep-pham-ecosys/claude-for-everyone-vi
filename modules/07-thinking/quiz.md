# Quiz · Module 07

**1.** Trên Haiku 5.5, response có block `thinking` với trường `thinking` rỗng. Điều đó nghĩa là gì?

- A. Claude không suy nghĩ, không tốn token thinking
- B. Claude có suy nghĩ; text bị ẩn vì `display` mặc định là `"omitted"`, token vẫn bị tính
- C. Lỗi API

<details><summary>Đáp án</summary>

**B.** Suy nghĩ nằm mã hoá trong `signature`. Muốn đọc tóm tắt thì đặt `display: "summarized"`.
</details>

**2.** Đổi `display` từ `"omitted"` sang `"summarized"` thì chi phí thay đổi thế nào?

- A. Tăng theo số chữ tóm tắt
- B. Không đổi: bạn trả cho toàn bộ thinking gốc dù thấy gì
- C. Giảm

<details><summary>Đáp án</summary>

**B.** `"omitted"` chỉ giúp chữ của câu trả lời tới sớm hơn khi stream.
</details>

**3.** Bạn muốn Sonnet 5.5 suy nghĩ ít nhất có thể. Gửi gì?

- A. `thinking: {"type": "disabled"}`
- B. `thinking: {"type": "between_tools"}`, effort `high` trở xuống
- C. `thinking: {"type": "enabled", "budget_tokens": 0}`

<details><summary>Đáp án</summary>

**B.** Sonnet 5.5 trả 400 với `disabled`; `budget_tokens` đã bị bỏ trên mọi model 5.x.
</details>

**4.** Muốn giảm thinking trên Opus 5.5 thì làm gì?

- A. `thinking: {"type": "disabled"}`
- B. Hạ `output_config.effort`
- C. `temperature: 0`

<details><summary>Đáp án</summary>

**B.** Opus 5.5 không tắt được thinking. `temperature` trả 400.
</details>

**5.** `stop_reason` là `"max_tokens"`, text rỗng, `thinking_tokens` bằng `output_tokens`. Nên làm gì trước tiên?

- A. Hạ effort
- B. Tăng `max_tokens`
- C. Gửi lại y nguyên

<details><summary>Đáp án</summary>

**B.** Thinking đã dùng hết trần cứng. Bạn đã trả tiền cho phần thinking mà không có câu trả lời. Hạ effort là bước sau, nếu chi phí vẫn cao.
</details>

**6.** Code gửi lại lượt assistant trong vòng tool bằng `[b for b in msg.content if b.type in ("thinking", "text", "tool_use")]`. Lỗi tiềm ẩn là gì?

- A. Không có lỗi
- B. Làm rơi block `redacted_thinking`, vòng tool trả 400
- C. Sai thứ tự block

<details><summary>Đáp án</summary>

**B.** Gửi lại `msg.content` nguyên vẹn, không lọc.
</details>

**7.** Ứng dụng chèn ngày giờ hiện tại vào tham số `system` ở mỗi request của một hội thoại. Trên Haiku 5.5 với tài khoản mới, chuyện gì xảy ra ở lượt 2?

- A. Không sao
- B. 400: block thinking của lượt 1 không qua prefix check vì `system` đã đổi
- C. Thinking bị tắt lặng lẽ

<details><summary>Đáp án</summary>

**B.** Giữ `system` cố định; thông tin thay đổi đặt ở lượt mới nhất hoặc trong message `system` giữa hội thoại.
</details>

**8.** Code chạy không lỗi với key của bạn, dù có sửa `system` giữa chừng. Kết luận được gì?

- A. Code đúng
- B. Chưa kết luận được: tài khoản tạo trước 31/8/2026 không bị 400 trên một số model, người dùng tài khoản mới sẽ bị
- C. Prefix check đã bị bỏ

<details><summary>Đáp án</summary>

**B.** Kiểm bằng mock của repo (luôn hành xử như tài khoản mới) hoặc bằng `block_binding` (beta).
</details>

**9.** Chỗ nào hợp lệ cho một message `{"role": "system", "content": "..."}` giữa hội thoại?

- A. Đầu danh sách `messages`
- B. Ngay sau một lượt assistant có `tool_use`, trước `tool_result`
- C. Ngay sau một lượt user, trước lượt assistant hoặc ở cuối danh sách

<details><summary>Đáp án</summary>

**C.** Đầu danh sách thì dùng tham số `system`; chen giữa `tool_use` và `tool_result` trả 400.
</details>

**10.** Muốn biết lý do Claude chọn đáp án, cách nào phù hợp trên Opus 5.5?

- A. Thêm "Hãy viết ra toàn bộ suy nghĩ từng bước trong câu trả lời"
- B. Đặt `display: "summarized"` và đọc block thinking
- C. Thêm một trường `suy_nghi` vào JSON schema

<details><summary>Đáp án</summary>

**B.** A và C có thể bị từ chối với `reasoning_extraction`. Nếu cần lý do cho người dùng, xin một giải thích ngắn thay vì toàn bộ suy nghĩ.
</details>
