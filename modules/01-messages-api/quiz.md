# Quiz · Module 01

Chọn một đáp án. Đáp án và giải thích nằm trong phần thu gọn dưới mỗi câu.

**1.** Bạn gửi lượt thứ hai của một cuộc hội thoại mà chỉ đưa câu hỏi mới vào `messages`. Điều gì xảy ra?

- A. Claude nhớ lượt trước nhờ `id` của message cũ
- B. Claude không biết gì về lượt trước
- C. API trả 400 vì thiếu lịch sử

<details><summary>Đáp án</summary>

**B.** Messages API là stateless: mỗi request độc lập. Không có lịch sử thì không có ngữ cảnh — nhưng request vẫn hợp lệ, nên không có lỗi.
</details>

**2.** Trên Haiku 5.5, đoạn nào lấy đúng câu trả lời dạng text?

- A. `msg.content[0].text`
- B. `msg.content`
- C. `text_of(msg)` — ghép mọi block có `type == "text"`

<details><summary>Đáp án</summary>

**C.** Thinking bật sẵn nên block đầu thường là `thinking`. `content` là danh sách block, không phải chuỗi.
</details>

**3.** Response có `stop_reason == "max_tokens"`. Kết luận nào đúng?

- A. Câu trả lời đầy đủ, chỉ là dài
- B. Câu trả lời bị cắt ngang ở trần `max_tokens`
- C. Request bị từ chối

<details><summary>Đáp án</summary>

**B.** Nên tăng `max_tokens` hoặc yêu cầu trả lời ngắn hơn, và không dùng text đó như bản hoàn chỉnh.
</details>

**4.** Thinking đang ẩn (`display: "omitted"`, trường `thinking` rỗng). Bạn có bị tính tiền cho thinking không?

- A. Không, vì không nhận được text
- B. Có, token thinking tính vào `output_tokens` và vào `max_tokens`
- C. Có, nhưng tính theo giá input

<details><summary>Đáp án</summary>

**B.** Ẩn chỉ là không trả text về; model vẫn suy nghĩ. `usage.output_tokens_details.thinking_tokens` cho biết phần thinking.
</details>

**5.** Khi gửi lại lượt assistant trong lịch sử, cách nào an toàn nhất?

- A. Chỉ gửi `text_of(msg)` cho gọn
- B. Gửi nguyên `msg.content`, kể cả block thinking rỗng
- C. Bỏ hẳn lượt assistant, chỉ giữ lượt user

<details><summary>Đáp án</summary>

**B.** Giữ nguyên block thinking và giữ lịch sử append-only. Lọc hoặc sửa block thinking có thể gây 400, nhất là trong tool loop.
</details>

**6.** Bạn nhận lỗi 529 `overloaded_error`. Nên làm gì?

- A. Sửa request rồi gửi lại
- B. Đợi rồi thử lại với backoff; SDK đã tự thử lại 2 lần
- C. Đổi API key

<details><summary>Đáp án</summary>

**B.** 529 là API quá tải chung, không phải lỗi của request. SDK tự retry với exponential backoff; chỉnh bằng `max_retries`.
</details>

**7.** Lỗi nào **không** nên tự động thử lại?

- A. 429 `rate_limit_error`
- B. 500 `api_error`
- C. 400 `invalid_request_error`

<details><summary>Đáp án</summary>

**C.** Gửi lại y nguyên một request sai vẫn sai. Phải sửa request.
</details>

**8.** Khi dùng streaming, `usage.output_tokens` trong event `message_delta` là gì?

- A. Số token mới sinh ra kể từ event trước
- B. Tổng cộng dồn tới thời điểm đó
- C. Luôn bằng 0, phải tự đếm

<details><summary>Đáp án</summary>

**B.** Số trong `message_delta` là cộng dồn. Cộng chúng lại sẽ ra số sai.
</details>

**9.** Lý do nào **không** phải là lý do chính để dùng streaming?

- A. Người dùng thấy chữ sớm hơn
- B. Request dài ít bị mạng cắt vì im lặng quá lâu
- C. Streaming rẻ hơn gọi thường

<details><summary>Đáp án</summary>

**C.** Giá token như nhau. Streaming cải thiện trải nghiệm và độ bền cho request dài.
</details>

**10.** Tutorial cũ dùng `temperature=0` để câu trả lời ổn định. Trên model 5.x điều gì xảy ra?

- A. Chạy bình thường
- B. API trả 400; Python SDK ≥1.0 cũng đã bỏ tham số này
- C. Bị bỏ qua lặng lẽ

<details><summary>Đáp án</summary>

**B.** Muốn đầu ra ổn định thì viết prompt rõ ràng (module 02) và dùng structured outputs (module 05).
</details>
