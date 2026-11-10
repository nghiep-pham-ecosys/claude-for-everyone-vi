# 05 · Structured outputs, PDF và Citations

**Loại:** Learn + Build · **Thời lượng:** khoảng 2,5 giờ · **Cần:** module 01–02 · **Chi phí:** $0 ở mock mode; dưới $0,01 nếu chạy thật với `claude-haiku-5-5` (giá kiểm 24/10/2026, xem [references.md](references.md))

## Mục tiêu

Sau module này bạn:

- Viết schema bằng Pydantic, gửi được qua structured outputs, và vẫn giữ ràng buộc (`ge`, `le`) ở phía code.
- Biết các giới hạn của JSON Schema trong structured outputs, kể cả giới hạn độ phức tạp tính gộp trên cả request.
- Gửi PDF cho Claude theo ba cách và ước tính được chi phí.
- Bật citations trên văn bản thuần, PDF và custom content; đọc đúng ba loại vị trí trích dẫn.
- Tự kiểm một citation có trỏ đúng chỗ trong tài liệu không.
- Lấy dữ liệu có cấu trúc **kèm trích dẫn** dù citations và structured outputs không dùng chung được.

| Learn | Build |
|---|---|
| Đọc mục 1–6, chạy 5 script trong `python/` | Làm 3 bài trong `exercises/`, rồi làm [capstone c2](../../capstones/c2-trich-xuat-pdf) |

## Vì sao học cái này

Phần lớn ứng dụng thật không cần Claude "trò chuyện". Chúng cần Claude **đọc tài liệu và trả dữ liệu** mà code dùng được ngay: một bảng số liệu, một phiếu đã điền, một câu trả lời có dẫn nguồn.

Hai câu hỏi luôn đi kèm:

1. **Dữ liệu có đúng định dạng không?** Structured outputs trả lời câu này: API đảm bảo JSON khớp schema.
2. **Dữ liệu lấy từ đâu?** Citations trả lời câu này: API trả về vị trí thật trong tài liệu, không phải lời model tự khai.

Không câu nào thay được câu kia. JSON đúng schema vẫn có thể chứa số bịa; một câu trích dẫn đúng vẫn có thể bị gán nhầm đại lượng. Module này dạy dùng cả hai, rồi **kiểm lại bằng code**.

## Tối thiểu chạy được

```bash
CLAUDE_MOCK=1 uv run python modules/05-structured-pdf-citations/python/03_citations_van_ban.py
```

| Script | Ý chính |
|---|---|
| [`01_pydantic_schema.py`](python/01_pydantic_schema.py) | Schema Pydantic → `transform_schema` → gửi; kiểm ràng buộc khi đọc |
| [`02_pdf.py`](python/02_pdf.py) | Gửi PDF base64; ước tính token; cách URL và Files API |
| [`03_citations_van_ban.py`](python/03_citations_van_ban.py) | Citations trên văn bản thuần, kiểm `char_location` |
| [`04_custom_content.py`](python/04_custom_content.py) | Custom content: mỗi block là một đơn vị trích dẫn |
| [`05_truong_kem_trich_dan.py`](python/05_truong_kem_trich_dan.py) | Lấy từng trường kèm trích dẫn mà không dùng structured outputs |

Ở mock mode, citations là "thật một nửa": mock đọc tài liệu bạn gửi (kể cả PDF) và trích những câu có ít nhất 2 con số, kèm vị trí đúng. Mock không hiểu câu hỏi, nên nó không chọn câu theo nội dung. Structured outputs ở mock trả giá trị tối thiểu theo schema (`"[MOCK]"`, `0`, phần tử đầu của `enum`).

## 1. Structured outputs, nhắc lại và đi sâu

Module 02 đã dạy `output_config.format`. Nhắc lại ba điều phải nhớ:

- Mọi `object` cần `additionalProperties: false`.
- Chỉ tin JSON khi `stop_reason == "end_turn"`. Với `max_tokens` JSON có thể bị cắt; với `refusal` nó có thể không khớp schema.
- Claude có thể đổi hoa thường của giá trị `enum`. So khớp không phân biệt hoa thường.

### Viết schema bằng Pydantic

Viết schema dict bằng tay dễ sai và dài. Cách gọn hơn là khai báo một lớp Pydantic, rồi để SDK chuyển nó thành schema gửi được:

```python
from anthropic import transform_schema

class PhepDo(BaseModel):
    mau: str
    gia_tri: float = Field(ge=0)

schema = transform_schema(PhepDo)   # thêm additionalProperties: false, bỏ "minimum"
```

`transform_schema` làm ba việc chính: thêm `additionalProperties: false` cho mọi object, **bỏ** các ràng buộc API không hỗ trợ (`minimum`, `maximum`, `minLength`...), và chép chúng vào `description` (ví dụ `{minimum: 0}`) để Claude vẫn đọc được.

**Vì sao vẫn phải kiểm trong code:** sau khi bỏ `minimum`, API không còn đảm bảo `gia_tri >= 0`. Nó chỉ đảm bảo `gia_tri` là số. Hãy đọc kết quả bằng `PhepDo.model_validate_json(...)`: Pydantic kiểm lại ràng buộc gốc. Nếu gửi thẳng `PhepDo.model_json_schema()`, schema còn `minimum` và thiếu `additionalProperties`, nên API trả 400 (`claude_vi` chặn trước).

SDK còn có `client.messages.parse(..., output_format=PhepDo)` làm cả hai bước. Repo dùng dict để bạn thấy rõ cái gì được gửi đi.

### Những gì schema không làm được

| Không hỗ trợ | Làm thay |
|---|---|
| `minimum`/`maximum`, `multipleOf` | Kiểm trong code (Pydantic) |
| `minLength`/`maxLength` | Kiểm trong code |
| `minItems` lớn hơn 1 | Kiểm trong code |
| Schema đệ quy | Làm phẳng cấu trúc |
| `pattern` có backreference (`\1`), lookahead/lookbehind, `\b` | Regex đơn giản, hoặc kiểm trong code |

### Giới hạn độ phức tạp

Structured outputs biên dịch schema thành một bộ ngữ pháp ép output. Schema càng phức tạp, biên dịch càng lâu, nên API đặt giới hạn **tính gộp trên mọi schema strict của một request** (`output_config.format` cộng mọi tool `strict: true`):

| Giới hạn | Giá trị |
|---|---|
| Tool strict | 20 |
| Tham số optional (không nằm trong `required`) | 24 |
| Tham số dùng union (`anyOf`, hoặc `type` là mảng như `["string", "null"]`) | 16 |

Vượt các giới hạn ẩn khác thì nhận 400 "Schema is too complex for compilation". Cách giảm, theo thứ tự: chỉ đặt strict cho tool thật sự cần; đưa tham số vào `required` nếu có giá trị mặc định hợp lý; làm phẳng object lồng nhau; tách thành nhiều request.

Chú ý: trong Pydantic, `ghi_chu: str | None = None` vừa là optional **vừa** là union, nên tính vào cả hai giới hạn. `claude_vi` đếm hai con số này và chặn trước khi gửi.

Lần đầu dùng một schema, request chậm hơn vì phải biên dịch. Bản biên dịch được cache 24 giờ kể từ lần dùng cuối; đổi cấu trúc schema thì mất cache, chỉ đổi `name`/`description` thì không.

## 2. PDF

**Cách API đọc PDF:** mỗi trang được chuyển thành ảnh, text của trang được rút ra và đưa kèm. Claude đọc cả hai, nên hiểu được bảng, biểu đồ, hình vẽ. Hệ quả về chi phí: mỗi trang tốn token text (thường 1.500–3.000 token tuỳ độ dày) **cộng** token ảnh. Không có phí riêng cho PDF. Muốn biết chính xác thì dùng token counting (module 06).

Ba cách đưa PDF vào block `document`:

| Nguồn | Khi nào dùng |
|---|---|
| `{"type": "base64", "media_type": "application/pdf", "data": ...}` | File ở máy, dùng một lần. Script 02 và capstone c2 dùng cách này |
| `{"type": "url", "url": "https://..."}` | PDF công khai trên mạng |
| `{"type": "file", "file_id": "file_..."}` | Tải lên một lần qua Files API, dùng lại nhiều request; giữ request nhỏ |

Giới hạn (kiểm 09/11/2026): request tối đa **128 MB** trên Claude API, tối đa **600 trang** (100 trang nếu context window của request dưới 1 triệu token). PDF không được đặt mật khẩu. PDF dày đặc có thể đầy context trước khi chạm giới hạn trang; khi đó tách PDF thành nhiều phần.

Mẹo từ docs: đặt PDF **trước** câu hỏi; dùng số trang hiển thị trong trình đọc PDF khi nhắc tới trang; xoay trang cho thẳng.

## 3. Citations: cơ chế

Bật `citations: {"enabled": true}` trên block `document`. API làm ba việc:

1. **Cắt tài liệu thành đơn vị trích dẫn.** Văn bản thuần và PDF được cắt theo câu. Custom content giữ nguyên từng block bạn đưa vào.
2. **Claude trả lời** thành nhiều block `text`. Block nào chứa một khẳng định có nguồn thì có danh sách `citations`.
3. **API tự điền `cited_text`** từ tài liệu gốc, nên trích dẫn luôn trỏ vào tài liệu có thật.

```text
content = [
  text("Theo phiếu, "),
  text("mẫu W2 có pH 6.4", citations=[char_location(cited_text="Mẫu W2 có ... pH 6.4.", 93, 127)]),
  text(" nên thấp hơn 7."),
]
```

Lợi về chi phí: `cited_text` **không** tính vào output token, và khi gửi lại ở lượt sau cũng không tính vào input token. Bật citations tốn thêm một ít input token (system prompt và việc cắt tài liệu).

Luật cần biết:

- Bật citations cho **tất cả hoặc không** document nào trong request. Bật lẫn lộn thì `claude_vi` chặn.
- `title` và `context` được gửi cho Claude nhưng **không** được trích dẫn. Dùng `context` để đặt metadata (ví dụ JSON mô tả nguồn).
- Chỉ trích được text. PDF scan không có lớp text thì không trích được.
- Stream: citation đến dưới dạng delta `citations_delta`, mỗi delta một citation để nối vào block text đang stream.
- Dùng được với prompt caching (đặt `cache_control` trên block document), token counting và batch.

## 4. Ba loại vị trí trích dẫn

| Loại tài liệu | `source` | Cắt theo | Loại citation | Chỉ số |
|---|---|---|---|---|
| Văn bản thuần | `{"type": "text", "media_type": "text/plain", "data": ...}` | Câu | `char_location` | Ký tự, **từ 0**, end không tính |
| PDF | base64 / URL / file | Câu | `page_location` | Trang, **từ 1**, end không tính |
| Custom content | `{"type": "content", "content": [blocks...]}` | Không cắt thêm | `content_block_location` | Block, **từ 0**, end không tính |

`document_index` đếm từ 0 trên **mọi** block document của request, xuyên qua mọi lượt message.

"End không tính" nghĩa là một câu nằm gọn ở trang 1 có `start_page_number=1, end_page_number=2`. Văn bản thuần thì `data[start:end] == cited_text` đúng như slice của Python. [`03_citations_van_ban.py`](python/03_citations_van_ban.py) kiểm đúng điều này.

**Khi nào dùng custom content:** danh sách gạch đầu dòng, bản ghi lời nói, nhật ký máy, các đoạn RAG mà bạn đã tự cắt. Cắt theo câu ở những dạng này dễ ra mảnh vô nghĩa. Với RAG (module 04): muốn Claude trích từng câu trong một đoạn thì mỗi đoạn là một document văn bản thuần; muốn trích nguyên đoạn thì đưa các đoạn vào một custom content document.

## 5. Citations và structured outputs không đi cùng nhau

Bật citations trên bất kỳ document nào **và** có `output_config.format` thì API trả 400. Lý do: citations phải chen các block trích dẫn vào giữa text, còn structured outputs ép text thành đúng một JSON.

Có hai cách lấy dữ liệu có cấu trúc kèm nguồn:

**Cách A: hai lượt** (capstone c2). Lượt 1 bật citations để lấy trích dẫn và vị trí. Lượt 2 gửi danh sách trích dẫn (không gửi lại PDF) kèm structured outputs, mỗi dòng JSON trỏ về id trích dẫn qua `enum`. Hợp khi cần bảng nhiều dòng, schema chặt.

**Cách B: một lượt, mỗi trường một dòng** (bài 3, theo docs). Xin Claude trả lời mỗi trường một dòng `ten: gia_tri` và trích nguồn từng dòng, rồi tự tách trong code:

1. Đọc block text theo thứ tự, nối vào dòng hiện tại; gặp xuống dòng thì sang dòng mới.
2. Gắn citations của một block vào mọi dòng chứa một phần text của block đó.
3. Bỏ dòng không có dấu hai chấm; tách ở dấu hai chấm **đầu tiên**; bỏ dòng có tên lạ.
4. Kiểm mỗi trường có giá trị và có ít nhất một trích dẫn. API không đảm bảo điều này.

Hợp khi chỉ cần vài trường phẳng, rẻ hơn một lượt.

Đừng viết "chỉ trả về JSON, không gì khác" trong prompt khi bật citations: request vẫn thành công nhưng có thể gần như không có trích dẫn nào.

## 6. Tự kiểm citation

API đảm bảo citation trỏ vào tài liệu bạn gửi. Vẫn nên kiểm lại bằng code khi:

- bạn lưu vị trí trích dẫn để hiển thị (ô highlight, link tới trang) và cần chắc chỉ số đúng quy ước;
- response đi qua cache, log hay fixture trước khi tới bạn;
- bạn ghép citation với dữ liệu khác (như bước 3 của capstone c2).

Cách kiểm theo từng loại nằm ở bài 2. Điều quan trọng hơn: **citation chỉ chứng minh câu trích có thật trong tài liệu**, không chứng minh Claude hiểu đúng câu đó. Muốn chặt hơn thì đối chiếu thêm giá trị (capstone c2 kiểm con số có nằm trong câu trích không) hoặc cho người duyệt.

## Bẫy thường gặp

- **Bật citations và `output_config.format` cùng lúc** → 400.
- **Gửi `model_json_schema()` thẳng cho API** → 400 vì còn `minimum`, thiếu `additionalProperties`. Dùng `transform_schema`.
- **Dùng `transform_schema` rồi quên kiểm ràng buộc.** API không còn đảm bảo `ge`/`le`.
- **Nhiều trường `str | None`** trên nhiều tool strict, cộng lại vượt 24 optional hoặc 16 union.
- **Nhầm quy ước chỉ số:** trang đếm từ 1, ký tự và block đếm từ 0; end luôn không tính.
- **Tin số trang do model tự viết trong text** thay vì `start_page_number` của citation.
- **Bật citations cho một số document, không bật cho số khác.**
- **Đặt nội dung cần trích vào `title`/`context`.** Hai trường này không được trích.
- **Prompt "chỉ trả JSON" khi bật citations** → gần như mất trích dẫn.
- **Gửi PDF scan không có lớp text** rồi chờ citations.
- **Gửi lại PDF ở mọi lượt.** Mỗi lần tốn lại token của cả PDF; dùng prompt caching (module 06) hoặc chỉ gửi phần trích.

## Điều gì đã thay đổi ở model 5.x

| Trước đây | Bây giờ |
|---|---|
| Prefill `{` để ép JSON | 400. Dùng `output_config.format` |
| `output_format` (beta, cần beta header) | `output_config.format`, không cần header. Python SDK ≥1.0 ném `TypeError` nếu truyền `output_format={...}` cho `client.beta.messages.create()` |
| Ép JSON bằng tool use với `tool_choice` `tool` | 400 trên Opus 5.5, Sonnet 5.5, Fable 5.1. Dùng structured outputs |
| Xin model tự ghi "(trang 3)" vào câu trả lời | Citations trả vị trí do API tính, `cited_text` không tốn output token |
| Request tối đa 32 MB | 128 MB trên Claude API (từ 28/10/2026) |

## Bài tập

```bash
CHAM=exercises uv run pytest modules/05-structured-pdf-citations -q
```

| Bài | Nội dung |
|---|---|
| [`bai1_phieu_nuoc.py`](exercises/bai1_phieu_nuoc.py) | Schema Pydantic có ràng buộc; `transform_schema`; kiểm lại khi đọc; chuẩn hoá enum |
| [`bai2_kiem_trich_dan.py`](exercises/bai2_kiem_trich_dan.py) | Đọc và tự kiểm `char_location`, `page_location`, `content_block_location` |
| [`bai3_truong_kem_trich_dan.py`](exercises/bai3_truong_kem_trich_dan.py) | Mỗi trường một dòng kèm trích dẫn; bộ tách theo thuật toán của docs |

Lời giải trong [`solutions/`](solutions/). Tự kiểm tra: [quiz.md](quiz.md). Nguồn: [references.md](references.md).

## Tiếp theo

[Capstone c2](../../capstones/c2-trich-xuat-pdf): ghép mọi thứ của module này thành pipeline trích bảng số liệu từ PDF, mỗi con số truy được về trang gốc. Sau đó là module 07 — Thinking.
