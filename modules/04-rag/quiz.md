# Quiz · Module 04

**1.** Kho tài liệu của bạn là 30 trang hướng dẫn (khoảng 20.000 token). Nên bắt đầu thế nào?

- A. Dựng RAG với vector database ngay
- B. Thử gửi cả kho vào prompt (có prompt caching), đo chi phí và chất lượng trước
- C. Fine-tune model

<details><summary>Đáp án</summary>

**B.** Kho nhỏ thì gửi cả là cách đơn giản nhất. RAG đáng công khi kho lớn hoặc chi phí gửi cả quá cao.
</details>

**2.** Câu hỏi "Máy báo E-17" và kho có đoạn "E-17: điện cực khô...". Cách tìm nào chắc ăn hơn?

- A. BM25, vì nó khớp đúng chuỗi "e-17"
- B. Chỉ embedding, vì nó hiểu nghĩa
- C. Như nhau

<details><summary>Đáp án</summary>

**A.** Embedding dễ hụt mã, số, thuật ngữ chính xác. Đó là lý do người ta kết hợp BM25 với embedding.
</details>

**3.** Trong BM25, vì sao từ "máy" gần như không đóng góp điểm trên sổ tay mẫu?

- A. Vì từ ngắn bị bỏ
- B. Vì "máy" xuất hiện ở nhiều đoạn nên idf thấp
- C. Vì BM25 bỏ danh từ

<details><summary>Đáp án</summary>

**B.** idf thưởng cho từ hiếm và gần như bỏ qua từ có ở khắp nơi.
</details>

**4.** Hai chuỗi "hiệu" trông giống hệt nhau nhưng `==` trả `False`. Nguyên nhân thường gặp?

- A. Lỗi Python
- B. Một chuỗi dùng ký tự dựng sẵn, chuỗi kia dùng chữ cái + dấu tổ hợp; cần chuẩn hoá NFC
- C. Khác font

<details><summary>Đáp án</summary>

**B.** Luôn `unicodedata.normalize("NFC", ...)` trước khi tách từ.
</details>

**5.** Đoạn "Thực hiện lại sau mỗi 8 giờ đo" không được tìm thấy cho câu hỏi về hiệu chuẩn máy pH. Cách sửa rẻ nhất?

- A. Đổi sang model lớn hơn
- B. Chép tiêu đề tài liệu và tên mục vào đầu đoạn trước khi lập chỉ mục
- C. Tăng `max_tokens`

<details><summary>Đáp án</summary>

**B.** Đoạn mất ngữ cảnh khi bị cắt. Thêm tiêu đề/mục không tốn token nào; nhờ Claude viết ngữ cảnh là bước tiếp theo nếu đo thấy cần.
</details>

**6.** BM25 cho đoạn A điểm 8,4; embedding cho đoạn B điểm 0,82. Ghép thế nào?

- A. Cộng thẳng điểm
- B. Lấy điểm cao nhất
- C. RRF: chỉ dùng thứ hạng của mỗi đoạn trong từng danh sách

<details><summary>Đáp án</summary>

**C.** Hai thang điểm khác nhau nên không so được; thứ hạng thì so được.
</details>

**7.** Vì sao chia `content` của `search_result` thành nhiều khối nhỏ?

- A. Để rẻ hơn
- B. Vì Claude trích nguyên khối; khối nhỏ thì trích dẫn sát với câu thật sự được dùng
- C. Bắt buộc mỗi khối tối đa 100 ký tự

<details><summary>Đáp án</summary>

**B.** Một khối lớn thì mọi trích dẫn đều trả về cả khối.
</details>

**8.** Tool tìm kiếm trả `[search_result, search_result, {"type": "text", "text": "Đã tìm 2 kết quả"}]` trong một `tool_result`. Chuyện gì xảy ra?

- A. Chạy bình thường
- B. Lỗi: đã có `search_result` thì mọi block trong `tool_result` phải là `search_result`
- C. Block text bị bỏ qua

<details><summary>Đáp án</summary>

**B.** Đặt ghi chú vào `content` của một `search_result` nếu cần.
</details>

**9.** Muốn chắc Claude luôn tìm trong sổ tay trước khi trả lời, trên Sonnet 5.5. Cách nào?

- A. `tool_choice: {"type": "tool", "name": "tim_so_tay"}`
- B. Tìm trước bằng code rồi gửi `search_result` cùng câu hỏi (như script 04)
- C. `temperature: 0`

<details><summary>Đáp án</summary>

**B.** `tool_choice` `tool`/`any` trả 400 trên Sonnet 5.5; `temperature` cũng trả 400.
</details>

**10.** Câu trả lời sai. Việc đầu tiên nên kiểm là gì?

- A. Đổi prompt `system`
- B. Đoạn chứa câu trả lời đúng có nằm trong các đoạn đã gửi cho Claude không
- C. Nâng effort

<details><summary>Đáp án</summary>

**B.** Claude không thể trả lời đúng từ đoạn không được tìm thấy. Sửa bước tìm trước, rồi mới sửa bước trả lời.
</details>
