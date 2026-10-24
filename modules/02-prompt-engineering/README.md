# 02 · Prompt engineering

**Loại:** Learn + Build · **Thời lượng:** khoảng 2,5 giờ · **Chi phí:** $0 ở mock mode; dưới $0,01 nếu chạy thật với `claude-haiku-5-5` (giá kiểm 24/10/2026, xem [references.md](references.md))

## Mục tiêu

Sau module này bạn:

- Viết prompt rõ ràng, có lý do, có định dạng đầu ra cụ thể.
- Đưa tài liệu dài vào prompt đúng chỗ, tách phần bằng thẻ XML.
- Dạy Claude bằng 3–5 ví dụ (few-shot).
- Ép định dạng bằng structured outputs thay cho prefill.
- Chọn mức effort thay cho `temperature`.

| Learn | Build |
|---|---|
| Đọc mục 1–6, chạy 5 script trong `python/` | Làm 3 bài trong `exercises/`, chấm bằng test |

## Vì sao học cái này

Cùng một model, prompt mơ hồ cho câu trả lời mơ hồ. Prompt engineering là cách rẻ nhất để tăng chất lượng: không đổi model, không thêm hạ tầng.

Nhưng trước khi sửa prompt, cần biết "tốt hơn" nghĩa là gì. Docs khuyên có sẵn ba thứ: **tiêu chí thành công rõ ràng**, **cách đo** theo tiêu chí đó, và **một bản prompt đầu tiên**. Không đo được thì không biết prompt mới có tốt hơn không (module 13 sẽ nói về evals).

## Tối thiểu chạy được

```bash
CLAUDE_MOCK=1 uv run python modules/02-prompt-engineering/python/01_ro_rang.py
```

| Script | Ý chính |
|---|---|
| [`01_ro_rang.py`](python/01_ro_rang.py) | Prompt mơ hồ và prompt rõ ràng; nói "vì sao" trong `system` |
| [`02_xml_tai_lieu.py`](python/02_xml_tai_lieu.py) | Nhiều tài liệu: XML, tài liệu ở trên, câu hỏi ở cuối |
| [`03_vi_du.py`](python/03_vi_du.py) | Few-shot: khối `<examples>` |
| [`04_structured_output.py`](python/04_structured_output.py) | JSON đúng schema bằng `output_config.format` |
| [`05_effort.py`](python/05_effort.py) | So sánh `low` / `medium` / `high` effort |

Ở mock mode, câu trả lời không đổi theo prompt — mock không "hiểu" prompt. Hãy đọc **prompt** mà script in ra. Chạy với key thật để thấy khác biệt về nội dung.

## 1. Rõ ràng và trực tiếp

Hãy coi Claude là một đồng nghiệp rất giỏi nhưng mới vào, chưa biết thói quen của bạn. Phép thử của docs: đưa prompt cho một người không biết gì về việc này. Nếu họ bối rối thì Claude cũng vậy.

- Nói rõ **người đọc**, **định dạng**, **độ dài**, **ràng buộc**.
- Khi thứ tự hay sự đầy đủ của các bước quan trọng, viết thành danh sách đánh số.
- Muốn Claude làm nhiều hơn mức tối thiểu thì phải nói ra; đừng mong nó tự đoán.

## 2. Nói "vì sao", không chỉ "cái gì"

So sánh hai cách viết:

- "KHÔNG BAO GIỜ dùng dấu ba chấm."
- "Câu trả lời sẽ được đọc bằng giọng máy, mà máy không biết đọc dấu ba chấm, nên đừng dùng nó."

Cách thứ hai tốt hơn. Khi biết lý do, Claude tự suy ra cả những quy tắc bạn chưa viết (ví dụ cũng tránh ký hiệu khó đọc khác). [`01_ro_rang.py`](python/01_ro_rang.py) đặt lý do ("in trên slide") vào `system`.

`system` là chỗ để đặt **vai trò** và bối cảnh chung. Chỉ một câu vai trò cũng đã tạo khác biệt.

## 3. Thẻ XML và tài liệu dài

Khi prompt trộn hướng dẫn, ngữ cảnh, ví dụ và dữ liệu, hãy bọc mỗi loại trong một thẻ riêng: `<instructions>`, `<context>`, `<input>`... Không có tên thẻ "chuẩn"; điều quan trọng là **đặt tên có nghĩa và dùng nhất quán**.

Với tài liệu dài (khoảng 20.000 token trở lên):

1. **Đặt tài liệu ở đầu**, câu hỏi và hướng dẫn ở cuối. Theo docs, đặt câu hỏi ở cuối có thể cải thiện chất lượng tới 30% với đầu vào nhiều tài liệu.
2. Mỗi tài liệu một thẻ `<document index="n">`, bên trong có `<source>` và `<document_content>`.

Xem [`02_xml_tai_lieu.py`](python/02_xml_tai_lieu.py). Bài 1 yêu cầu bạn viết hàm dựng cấu trúc này.

## 4. Dạy bằng ví dụ (few-shot)

Ví dụ là cách chắc nhất để cố định định dạng, giọng văn và cấu trúc. Theo docs, ví dụ tốt phải:

- **Sát thực tế** — giống dữ liệu thật bạn sẽ gặp.
- **Đa dạng** — phủ các trường hợp biên. Nếu mọi ví dụ cùng một đầu ra, Claude sẽ học nhầm "luôn trả X".
- **Có cấu trúc** — mỗi ví dụ trong `<example>`, cả khối trong `<examples>`.

Docs khuyên **3–5 ví dụ**. [`03_vi_du.py`](python/03_vi_du.py) có một ví dụ "khó" ("Mọi thứ ổn.") để dạy nhãn `khac`.

## 5. Ép định dạng: structured outputs thay cho prefill

Tutorial cũ ép JSON bằng cách **prefill**: kết thúc `messages` bằng lượt assistant `"{"`. Trên model 5.x việc này trả **400**.

Cách thay thế là **structured outputs**: truyền JSON schema vào `output_config.format`, và API đảm bảo text trả về khớp schema.

```python
client.create(
    messages=[...],
    output_config={"format": {"type": "json_schema", "schema": {
        "type": "object",
        "properties": {"nhom": {"type": "string", "enum": ["a", "b"]}},
        "required": ["nhom"],
        "additionalProperties": False,
    }}},
)
data = json.loads(text_of(msg))
```

Những điều cần nhớ (docs Structured outputs):

- Mọi `object` phải có `additionalProperties: false`.
- **Không** hỗ trợ `minimum`/`maximum`, `minLength`/`maxLength`, `multipleOf`, và `minItems` lớn hơn 1. Muốn ràng buộc giá trị thì kiểm trong code sau khi nhận kết quả. `claude_vi` chặn các từ khoá này trước khi gửi.
- Chỉ tin JSON khi `stop_reason == "end_turn"`. Với `max_tokens` JSON có thể bị cắt; với `refusal` nó có thể không khớp schema.
- Claude **có thể đổi hoa/thường** của giá trị `enum` (ví dụ `"Tot"` thay vì `"tot"`). So khớp không phân biệt hoa thường.
- Trường bắt buộc đứng trước, trường tuỳ chọn đứng sau, theo thứ tự trong schema.

Python SDK còn có `client.messages.parse(..., output_format=PydanticModel)`. Repo dùng schema dạng dict cho dễ thấy cái gì được gửi đi.

Các cách khác để bỏ prefill, theo docs:

- Muốn bỏ câu mở đầu "Dưới đây là..." thì yêu cầu thẳng trong `system`.
- Muốn tiếp tục một câu trả lời bị cắt thì đưa đoạn cuối vào lượt **user** và yêu cầu viết tiếp.

## 6. Effort thay cho temperature

`temperature`, `top_p`, `top_k` đã bị bỏ. Núm vặn mới là `output_config.effort`: `low`, `medium`, `high`, `xhigh`, `max`.

- Effort tác động lên **mọi** token output: độ dài, số lần gọi tool, và độ sâu thinking.
- Mặc định: `medium` trên Haiku 5.5 và Opus 5.5; `high` trên Sonnet 5.5 và Fable 5.1.
- `low` hợp với việc đơn giản, cần nhanh, số lượng lớn. `high` hợp với việc cần làm đúng chỉ dẫn chặt chẽ. Chỉ dùng `xhigh`/`max` khi đo thấy chất lượng tăng thật.
- Effort là **tín hiệu hành vi**, không phải ngân sách token cứng. `max_tokens` mới là trần cứng.
- `"adaptive"` là chế độ thinking, **không** phải mức effort.

[`05_effort.py`](python/05_effort.py) so sánh số token thinking giữa các mức (ở mock chỉ minh hoạ xu hướng).

## 7. Chia nhỏ việc lớn (prompt chaining)

Việc nhiều bước (đọc → trích → tóm tắt → kiểm tra) thường tốt hơn khi tách thành nhiều lời gọi, mỗi lời gọi một việc, đầu ra bước trước làm đầu vào bước sau. Capstone c2 dùng đúng cách này: một lượt lấy trích dẫn, một lượt chuyển thành JSON.

## Bẫy thường gặp

- **Sửa prompt mà không có cách đo.** Mỗi lần chạy thử trông "có vẻ tốt hơn" không phải là bằng chứng.
- **Chỉ nói "đừng làm X".** Nói nên làm gì thay thế ("viết thành đoạn văn liền mạch" thay vì "đừng dùng markdown").
- **Quy tắc không có lý do.** Claude chỉ tuân theo đúng chữ, không suy rộng ra được.
- **Ví dụ quá giống nhau**, hoặc chỉ có 1 ví dụ.
- **Câu hỏi đặt trước tài liệu dài.**
- **Thẻ XML đặt tên lung tung**, mỗi chỗ một kiểu.
- **Prefill để ép JSON**, hoặc dùng `temperature=0` cho "ổn định". Cả hai trả 400 trên model 5.x.
- **Tin JSON mà không kiểm `stop_reason`.**
- **Thêm `minimum`/`maxLength` vào schema** rồi bất ngờ vì lỗi 400.
- **So enum phân biệt hoa thường.**

## Điều gì đã thay đổi ở model 5.x

| Trước đây | Bây giờ |
|---|---|
| Prefill `{"role": "assistant", "content": "{"}` để ép JSON | 400. Dùng structured outputs (`output_config.format`) |
| Prefill `"Dưới đây là bản tóm tắt:"` để bỏ câu mở đầu | 400. Yêu cầu thẳng trong `system` |
| `temperature=0` cho câu trả lời ổn định | 400. Prompt rõ ràng + structured outputs; điều chỉnh công sức bằng `effort` |
| `output_format` (beta) | `output_config.format`, không cần beta header |
| Phải nhắc "hãy chi tiết" | Model mới nói ngắn gọn hơn, có thể bỏ phần tóm tắt nếu không được yêu cầu |

## Bài tập

```bash
CHAM=exercises uv run pytest modules/02-prompt-engineering -q
```

| Bài | Nội dung |
|---|---|
| [`bai1_tai_lieu.py`](exercises/bai1_tai_lieu.py) | Dựng prompt nhiều tài liệu: XML, tài liệu trước, câu hỏi cuối |
| [`bai2_vi_du.py`](exercises/bai2_vi_du.py) | Khối few-shot, kiểm số lượng 3–5 và tính đa dạng |
| [`bai3_phan_loai.py`](exercises/bai3_phan_loai.py) | Phân loại bằng structured outputs; kiểm `stop_reason`; chuẩn hoá hoa thường của enum |

Lời giải trong [`solutions/`](solutions/). Tự kiểm tra: [quiz.md](quiz.md). Nguồn: [references.md](references.md).

## Tiếp theo

Module 03 — Tool use: cho Claude gọi hàm của bạn.
