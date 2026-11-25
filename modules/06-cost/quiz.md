# Quiz · Module 06

**1.** `usage` có `output_tokens: 300` và `output_tokens_details.thinking_tokens: 200`. Bạn trả tiền output cho bao nhiêu token?

- A. 500
- B. 300
- C. 100

<details><summary>Đáp án</summary>

**B.** Thinking đã nằm trong `output_tokens`. Cộng thêm 200 là tính hai lần.
</details>

**2.** Request có cache trả `input_tokens: 40`, `cache_read_input_tokens: 2000`, `cache_creation_input_tokens: 0`. Prompt dài bao nhiêu token?

- A. 40
- B. 2.000
- C. 2.040

<details><summary>Đáp án</summary>

**C.** Tổng input = đọc cache + ghi cache + `input_tokens`. `input_tokens` chỉ là phần sau breakpoint cuối.
</details>

**3.** Bạn đặt `cache_control` lên block chứa giờ hiện tại, ở cuối system prompt. Chuyện gì xảy ra?

- A. Cache hoạt động bình thường
- B. Lần nào cũng ghi cache cả prefix, không bao giờ đọc được, nên tốn hơn không dùng cache
- C. API trả 400

<details><summary>Đáp án</summary>

**B.** Block đổi mỗi lần nên prefix mỗi lần mỗi khác. Đặt breakpoint ở cuối phần **không đổi**, trước block giờ.
</details>

**4.** System prompt của bạn 300 token, có `cache_control`, chạy trên Haiku 5.5. Sau lần gọi đầu, `cache_creation_input_tokens` bằng 0. Vì sao?

- A. Lỗi cấu hình, API sẽ trả 400 lần sau
- B. Prompt ngắn hơn ngưỡng 512 token nên không được cache; API không báo lỗi
- C. Cache chỉ có ở Opus

<details><summary>Đáp án</summary>

**B.** Dưới ngưỡng thì không cache và không báo gì. Hãy kiểm `usage` sau lần gọi đầu.
</details>

**5.** Với cache 1 giờ (ghi 2x giá input), cần đọc lại ít nhất bao nhiêu lần để rẻ hơn không cache?

- A. 1
- B. 2
- C. 10

<details><summary>Đáp án</summary>

**B.** Ghi 2x + 1 lần đọc vẫn đắt hơn 2 lần gửi thường. Từ lần đọc thứ hai thì rẻ hơn. Cache 5 phút (1,25x) hoà vốn sau 1 lần đọc.
</details>

**6.** `count_tokens` khác `create` ở điểm nào?

- A. Không nhận `max_tokens`, không tạo message, không dùng cache, miễn phí nhưng có giới hạn request riêng
- B. Tính tiền như input token
- C. Trả cả số token output dự kiến

<details><summary>Đáp án</summary>

**A.** Số đếm là ước tính cho input. Trần output thì bạn tự tính từ `max_tokens`.
</details>

**7.** Bạn đếm một prompt bằng model cũ được 10.000 token, rồi dùng số đó để ước tính chi phí trên Opus 5.5. Sai ở đâu?

- A. Không sai, token là như nhau
- B. Model từ 4.7 trở đi dùng tokenizer mới, cho nhiều hơn khoảng 30% token (tới khoảng 35% với Opus 5.5); phải đếm lại bằng đúng model
- C. Opus 5.5 không hỗ trợ đếm token

<details><summary>Đáp án</summary>

**B.** `count_tokens` đếm theo tokenizer của model bạn truyền vào.
</details>

**8.** Bạn gửi batch 3 request `a`, `b`, `c`. Kết quả về theo thứ tự `c`, `a`, `b`. Làm gì?

- A. Báo lỗi cho API
- B. Ghép theo `custom_id`; thứ tự kết quả không được bảo đảm
- C. Gửi lại batch

<details><summary>Đáp án</summary>

**B.** Mỗi request cần `custom_id` riêng (1–64 ký tự chữ, số, `-`, `_`).
</details>

**9.** Một request trong batch có `params` sai. Bạn biết lúc nào, và có trả tiền không?

- A. Ngay khi tạo batch; có trả tiền
- B. Khi cả batch xong, request đó là `errored`; không trả tiền cho nó
- C. Không bao giờ biết

<details><summary>Đáp án</summary>

**B.** `params` được kiểm bất đồng bộ. Vì vậy hãy kiểm request trước khi gửi (`client.batch_create` làm việc này). Chỉ `succeeded` bị tính tiền.
</details>

**10.** Bật message threads cho một hội thoại 20 lượt có làm hoá đơn giảm không?

- A. Có, chỉ trả tiền cho message mới
- B. Không tự giảm: thread làm request nhỏ hơn, giá không đổi; muốn rẻ hơn thì gửi `cache_control` cấp cao nhất ở mọi request của thread
- C. Có, thread giảm 50% như batch

<details><summary>Đáp án</summary>

**B.** Docs: thread không đổi giá và không tự bật cache. Thread cũng hết hạn sau 5 phút không dùng, hoặc API không continue được vì lý do khác: continue nhận 404 `thread_not_found` thì gửi lại cả hội thoại.
</details>
