# Quiz · Module 03

**1.** Ai chạy hàm khi Claude trả về một block `tool_use` cho tool bạn tự định nghĩa?

- A. Claude chạy trên máy chủ Anthropic
- B. Code của bạn
- C. SDK tự chạy mà không cần bạn viết gì

<details><summary>Đáp án</summary>

**B.** Claude chỉ trả về yêu cầu (`name`, `input`). Tool runner của SDK có thể tự động hoá vòng lặp, nhưng hàm vẫn là code của bạn.
</details>

**2.** Theo docs, yếu tố nào quan trọng nhất cho chất lượng tool use?

- A. Tên tool ngắn
- B. Mô tả tool thật chi tiết
- C. Có `input_examples`

<details><summary>Đáp án</summary>

**B.** Viết ít nhất 3–4 câu: tool làm gì, khi nào dùng, tham số nghĩa là gì, giới hạn ra sao.
</details>

**3.** Tên tool nào hợp lệ?

- A. `tra cứu AQI`
- B. `moi_truong_tra_aqi`
- C. `tra.aqi`

<details><summary>Đáp án</summary>

**B.** Tên phải khớp `^[a-zA-Z0-9_-]{1,128}$`.
</details>

**4.** Claude trả về 2 block `tool_use` trong một response. Gửi kết quả thế nào?

- A. Hai lượt user, mỗi lượt một `tool_result`
- B. Một lượt user chứa cả hai `tool_result`
- C. Chỉ cần trả kết quả của tool đầu tiên

<details><summary>Đáp án</summary>

**B.** Mỗi `tool_use` cần một `tool_result`, tất cả trong lượt user ngay sau.
</details>

**5.** Lượt user nào gây lỗi 400?

- A. `[tool_result, text]`
- B. `[text, tool_result]`

<details><summary>Đáp án</summary>

**B.** Các block `tool_result` phải đứng đầu.
</details>

**6.** Bạn lọc `msg.content` chỉ giữ `text` và `tool_use` trước khi gửi lại trong vòng lặp tool. Điều gì xảy ra trên model 5.x?

- A. Chạy bình thường, tiết kiệm token
- B. Lỗi 400 vì block thinking của lượt assistant mới nhất bị sửa/bỏ

<details><summary>Đáp án</summary>

**B.** Gửi lại `msg.content` nguyên vẹn.
</details>

**7.** Trên `claude-sonnet-5-5`, bạn muốn đảm bảo `input` của tool luôn đúng kiểu. Làm gì?

- A. `tool_choice={"type": "any"}`
- B. `"strict": true` trên định nghĩa tool
- C. Thêm "NHỚ ĐIỀN ĐÚNG KIỂU" vào prompt

<details><summary>Đáp án</summary>

**B.** A trả 400 trên Sonnet 5.5. C không đảm bảo được gì.
</details>

**8.** Tool của bạn ném `ConnectionError`. Cách xử lý tốt nhất?

- A. Để exception làm dừng chương trình
- B. Gửi `tool_result` rỗng
- C. Gửi `tool_result` với `"is_error": true` và mô tả lỗi kèm gợi ý bước tiếp theo

<details><summary>Đáp án</summary>

**C.** Claude sẽ dùng thông tin đó để thử cách khác hoặc báo cho người dùng.
</details>

**9.** Kết quả tool là nội dung một trang web. Nên đặt nó ở đâu?

- A. Trong `system` để Claude coi trọng
- B. Trong `tool_result`
- C. Trong block text của user

<details><summary>Đáp án</summary>

**B.** Nội dung bên ngoài là dữ liệu không đáng tin và có thể chứa chỉ dẫn độc hại. Giữ nó trong `tool_result`.
</details>

**10.** Vì sao vòng lặp tool cần giới hạn số lượt?

- A. API giới hạn 3 lượt
- B. Để agent không lặp vô hạn và tốn tiền khi có sự cố
- C. Không cần giới hạn

<details><summary>Đáp án</summary>

**B.**
</details>
