# Quiz · Module 02

**1.** Theo docs, bạn nên có gì **trước khi** bắt đầu sửa prompt?

- A. Một model mạnh hơn
- B. Tiêu chí thành công, cách đo theo tiêu chí đó, và một bản prompt đầu tiên
- C. Ít nhất 10 ví dụ

<details><summary>Đáp án</summary>

**B.** Không đo được thì không biết bản sửa có tốt hơn không.
</details>

**2.** Cách viết nào hiệu quả hơn?

- A. "KHÔNG ĐƯỢC dùng dấu ba chấm."
- B. "Văn bản sẽ được đọc bằng giọng máy, mà máy không đọc được dấu ba chấm, nên đừng dùng nó."

<details><summary>Đáp án</summary>

**B.** Có lý do thì Claude tự suy rộng ra các trường hợp tương tự.
</details>

**3.** Prompt có một tài liệu 50.000 token và một câu hỏi. Sắp xếp thế nào?

- A. Câu hỏi trước, tài liệu sau
- B. Tài liệu trước, câu hỏi ở cuối
- C. Thứ tự không ảnh hưởng

<details><summary>Đáp án</summary>

**B.** Theo docs, đặt câu hỏi ở cuối có thể cải thiện chất lượng tới 30% với đầu vào nhiều tài liệu.
</details>

**4.** Docs khuyên dùng bao nhiêu ví dụ few-shot?

- A. 1
- B. 3–5
- C. Càng nhiều càng tốt, tối thiểu 20

<details><summary>Đáp án</summary>

**B.** Ví dụ phải sát thực tế, đa dạng, và bọc trong `<example>`.
</details>

**5.** Cả 4 ví dụ của bạn đều có đầu ra là `"tich_cuc"`. Nguy cơ là gì?

- A. Không có nguy cơ gì
- B. Claude học nhầm khuôn mẫu "luôn trả tich_cuc"
- C. API trả 400

<details><summary>Đáp án</summary>

**B.** Ví dụ cần đa dạng, phủ cả các trường hợp biên.
</details>

**6.** Trên Haiku 5.5, cách nào ép được đầu ra là JSON đúng schema?

- A. Prefill lượt assistant bằng `"{"`
- B. `temperature=0` và dặn "chỉ trả JSON"
- C. `output_config.format` với `type: "json_schema"`

<details><summary>Đáp án</summary>

**C.** A và B đều trả 400 trên model 5.x.
</details>

**7.** Schema nào sẽ bị structured outputs từ chối?

- A. `{"type": "object", "properties": {"n": {"type": "integer"}}, "required": ["n"], "additionalProperties": false}`
- B. `{"type": "object", "properties": {"n": {"type": "integer", "minimum": 1}}, "required": ["n"], "additionalProperties": false}`

<details><summary>Đáp án</summary>

**B.** `minimum` không được hỗ trợ. Hãy kiểm khoảng giá trị trong code sau khi nhận kết quả.
</details>

**8.** Response structured output có `stop_reason == "max_tokens"`. Nên làm gì?

- A. `json.loads` như bình thường
- B. Coi như không dùng được: JSON có thể bị cắt dở; tăng `max_tokens` rồi gọi lại

<details><summary>Đáp án</summary>

**B.**
</details>

**9.** Mức effort mặc định của `claude-haiku-5-5` là gì?

- A. `low`
- B. `medium`
- C. `high`

<details><summary>Đáp án</summary>

**B.** Haiku 5.5 và Opus 5.5 mặc định `medium`; Sonnet 5.5 và Fable 5.1 mặc định `high`.
</details>

**10.** Câu nào về effort là **sai**?

- A. Effort ảnh hưởng cả text, lời gọi tool và thinking
- B. Effort là một ngân sách token cứng, không bao giờ vượt
- C. `"adaptive"` là chế độ thinking, không phải mức effort

<details><summary>Đáp án</summary>

**B.** Effort là tín hiệu hành vi. Trần cứng là `max_tokens`.
</details>
