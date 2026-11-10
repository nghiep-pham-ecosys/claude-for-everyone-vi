# Quiz · Module 05

**1.** Bạn gửi `transform_schema(PhepDo)` với `gia_tri: float = Field(ge=0)`. API đảm bảo điều gì về `gia_tri`?

- A. `gia_tri` là số và không âm
- B. `gia_tri` là số; ràng buộc không âm chỉ nằm trong description, phải tự kiểm
- C. Không đảm bảo gì

<details><summary>Đáp án</summary>

**B.** `transform_schema` bỏ `minimum` khỏi schema vì API không hỗ trợ, và chép nó vào description. Đọc kết quả bằng `PhepDo.model_validate_json` để kiểm lại.
</details>

**2.** Một request có `output_config.format` với 10 trường optional, và 3 tool `strict: true`, mỗi tool 5 trường optional. Chuyện gì xảy ra?

- A. Chạy bình thường vì mỗi schema đều dưới 24
- B. Lỗi 400 vì tổng 25 trường optional vượt giới hạn 24 tính gộp
- C. API tự bỏ strict ở tool thứ ba

<details><summary>Đáp án</summary>

**B.** Giới hạn tính gộp trên mọi schema strict của request. Cách sửa: đưa bớt vào `required`, bỏ strict ở tool không cần, hoặc tách request.
</details>

**3.** Bật citations và đặt `output_config.format` trong cùng request thì sao?

- A. JSON có thêm trường citations
- B. Lỗi 400
- C. Citations bị bỏ qua lặng lẽ

<details><summary>Đáp án</summary>

**B.** Citations phải chen block trích dẫn vào text, không hợp với JSON bị ép theo schema. Tách hai lượt, hoặc xin mỗi trường một dòng có trích dẫn.
</details>

**4.** Một câu nằm gọn ở trang 3 của PDF. Citation của nó có giá trị nào?

- A. `start_page_number=2, end_page_number=3`
- B. `start_page_number=3, end_page_number=3`
- C. `start_page_number=3, end_page_number=4`

<details><summary>Đáp án</summary>

**C.** Trang đếm từ 1, end không tính.
</details>

**5.** Bạn có nhật ký máy đo, mỗi dòng một sự kiện, và muốn Claude trích nguyên từng dòng. Dùng loại document nào?

- A. Văn bản thuần, nối các dòng bằng `\n`
- B. Custom content, mỗi dòng một block text
- C. PDF

<details><summary>Đáp án</summary>

**B.** Custom content không bị cắt thêm, mỗi block là một đơn vị trích dẫn. Văn bản thuần bị cắt theo câu, dòng không có dấu chấm có thể bị gộp hoặc cắt lạ.
</details>

**6.** Bạn đặt mã thí nghiệm vào trường `context` của document. Claude có trích dẫn được mã đó không?

- A. Có
- B. Không: `title` và `context` được gửi cho Claude nhưng không được trích

<details><summary>Đáp án</summary>

**B.** Nội dung cần trích phải nằm trong `source`.
</details>

**7.** Bật citations, prompt viết "Chỉ trả về một object JSON, không gì khác". Kết quả có thể là gì?

- A. Lỗi 400
- B. Request thành công nhưng có rất ít hoặc không có trích dẫn
- C. JSON kèm trích dẫn đầy đủ

<details><summary>Đáp án</summary>

**B.** Docs cảnh báo đúng trường hợp này. Xin mỗi trường một dòng `ten: gia_tri` và trích nguồn từng dòng.
</details>

**8.** Khi tách dòng `gio_lay: 08:20`, nên làm gì?

- A. Tách ở mọi dấu hai chấm
- B. Tách ở dấu hai chấm đầu tiên
- C. Bỏ dòng vì có nhiều dấu hai chấm

<details><summary>Đáp án</summary>

**B.** Tên trường không chứa dấu hai chấm, giá trị thì có thể có.
</details>

**9.** PDF 2 trang. Ước tính input token thế nào?

- A. Chỉ tính số ký tự text
- B. Khoảng 1.500–3.000 token text mỗi trang, cộng token ảnh của mỗi trang
- C. Mỗi trang cố định 1.000 token

<details><summary>Đáp án</summary>

**B.** API chuyển mỗi trang thành ảnh và đưa kèm text rút ra. Muốn số chính xác thì dùng token counting.
</details>

**10.** Bước kiểm chứng thấy câu trích có thật ở trang 1 và chứa con số 276. Điều đó chứng minh gì?

- A. 276 chắc chắn là yield strength của mẫu A1
- B. 276 có xuất hiện trong một câu có thật ở trang 1; chưa chứng minh nó được gán đúng đại lượng
- C. Không chứng minh gì

<details><summary>Đáp án</summary>

**B.** Citation chứng minh nguồn, không chứng minh cách hiểu. Muốn chặt hơn thì kiểm thêm tên đại lượng hoặc cho người duyệt.
</details>
