# 06 · Chi phí (phần cơ bản)

**Loại:** Learn · **Thời lượng:** khoảng 30 phút · **Cần:** module 01 (mục 5) và 07 (mục 4) · **Chi phí:** $0 ở mock mode; dưới $0,01 nếu chạy thật với `claude-haiku-5-5` (giá trong [`config/models.yaml`](../../config/models.yaml), xem [references.md](references.md))

> Đây là phần đầu của module 06: token vào/ra, giá theo model, ước tính trước khi gọi và đọc chi phí sau khi gọi. Prompt caching chỉ được giới thiệu khái niệm. Đếm token bằng API, giá cache, Batch API và message threads sẽ ở các phần sau.

## Mục tiêu

Sau phần này bạn:

- Biết một lời gọi bị tính tiền theo những con số nào trong `msg.usage`.
- Đọc giá từ `config/models.yaml` thay vì gõ số vào code.
- Tính được **trần chi phí output** của một lời gọi **trước khi** gửi.
- Tách chi phí sau khi gọi thành input, output và phần thinking nằm trong output.
- Biết `estimate_cost_usd(msg)` bỏ sót những gì, nhất là cache.

| Learn | Build |
|---|---|
| Đọc mục 1–4, chạy script trong `python/` | Chưa có bài tập; test trong `tests/` kiểm script |

## Vì sao học cái này

Chi phí của một ứng dụng Claude không nằm ở một lời gọi. Nó nằm ở lời gọi đó nhân với số người dùng, số lượt hội thoại và số lần retry. Một con số nhỏ như $0,0005 thành đáng kể khi nhân lên hàng triệu.

Bạn cần hai thói quen. Trước khi gọi: biết lời gọi này **tốn tối đa** bao nhiêu. Sau khi gọi: biết nó **đã tốn** bao nhiêu và vì sao. Module này dạy cả hai, chỉ bằng `usage` và bảng giá của repo.

## Tối thiểu chạy được

```bash
CLAUDE_MOCK=1 uv run python modules/06-cost/python/01_uoc_tinh_chi_phi.py
```

| Script | Ý chính |
|---|---|
| [`01_uoc_tinh_chi_phi.py`](python/01_uoc_tinh_chi_phi.py) | Bảng giá từ config, trần output theo `max_tokens`, tách chi phí từ `usage`, so với `estimate_cost_usd` |

Script không cần API key và không gọi mạng. Mock trả `usage` giả lập: số token thinking đổi theo `effort`, nên bạn thấy effort là một "núm vặn" chi phí. Các con số token là của mock, không phải số thật.

## 1. Bạn trả tiền cho những gì

`msg.usage` có ba con số chính (module 01, mục 5):

- `input_tokens`: mọi thứ bạn gửi, gồm `system` và toàn bộ lịch sử hội thoại.
- `output_tokens`: mọi thứ Claude sinh ra, **gồm cả thinking**, kể cả khi text thinking bị ẩn.
- `output_tokens_details.thinking_tokens`: phần thinking nằm trong `output_tokens`. Đừng cộng nó thêm lần nữa.

Công thức, giá tính theo triệu token (MTok):

```text
chi phí = input_tokens × giá input / 1.000.000 + output_tokens × giá output / 1.000.000
```

Hai hệ quả:

- **Hội thoại dài thì input lớn dần.** Mỗi lượt gửi lại toàn bộ lịch sử, và trên model 5.x lịch sử còn giữ cả block thinking cũ (module 07, mục 5).
- **Output thường đắt hơn input** với cùng số token. Xem bảng giá ở mục 2.

## 2. Giá theo model: đọc từ config

Giá nằm ở một chỗ duy nhất: `price_per_mtok` trong [`config/models.yaml`](../../config/models.yaml). Script đọc nó bằng `load_models()`:

```python
from claude_vi import load_models

gia = load_models()["models"][model]["price_per_mtok"]   # {"input": ..., "output": ...}
```

Vì sao không gõ số vào code: giá đổi theo thời gian và theo model mới. Khi đổi, chỉ YAML đổi; script, test và `estimate_cost_usd` đi theo. Model chưa có giá trong config thì `estimate_cost_usd` trả `nan`, không đoán.

Phần 1 của script in bảng giá các model `active` trong config. Lưu ý từ chính config: giá của `claude-haiku-5-5` là mức **thấp nhất** ("from"); prompt trên 100.000 token có giá cao hơn (module 01, references).

## 3. Ước tính trước khi gọi

`max_tokens` là trần **cứng** cho mọi token output của một lời gọi: thinking + text (module 07, mục 4). Nên trước khi gửi, bạn đã biết:

```text
chi phí output tối đa = max_tokens × giá output / 1.000.000
```

Đó là việc của `tran_chi_phi_output(model, max_tokens)` trong script. Với `MAX_TOKENS=1024` mặc định của repo, bảng ở phần 1 của script cho thấy trần này khác nhau rất xa giữa các model.

Phần input khó hơn: bạn chưa biết số token trước khi gửi. Có hai cách:

- **Đo một lần, dùng lại:** gọi một request giống hệt (hoặc chạy mock với fixture ghi từ API thật) rồi đọc `input_tokens`.
- **Đếm token bằng API:** SDK có `client.messages.count_tokens(...)`. `claude_vi` và mock chưa hỗ trợ; phần sau của module 06 sẽ dạy.

Ước tính trước khi gọi dùng để **chặn**, không để báo cáo. Ví dụ: từ chối một job nếu trần chi phí của cả loạt request vượt ngân sách.

## 4. Đọc chi phí sau khi gọi

`tach_chi_phi(msg)` trong script trả về:

| Khoá | Nghĩa |
|---|---|
| `input` | `input_tokens × giá input` |
| `output` | `output_tokens × giá output` (đã gồm thinking) |
| `thinking` | phần của `output` do thinking, chỉ để xem, không cộng thêm |
| `tong` | `input + output`, bằng `estimate_cost_usd(msg)` |
| `token_cache_chua_tinh` | số token cache trong `usage` mà ước tính chưa tính |

Phần 3 của script gọi cùng một câu hỏi với effort `low` và `high`. Input không đổi; output và phần thinking đổi theo effort. Muốn giảm chi phí trên cả loạt request thì hạ effort; muốn chắc chắn không vượt một mức thì đặt `max_tokens` (module 07, mục 4).

## 5. Prompt caching: khái niệm

**Prompt caching** (lưu đệm prompt): khi nhiều request bắt đầu bằng cùng một phần dài (system prompt, tài liệu, danh sách tool), API có thể lưu phần đầu đó và dùng lại thay vì xử lý lại từ đầu. Khi đó `usage` có thêm hai trường (kiểm trong SDK `anthropic` 1.17.0):

- `cache_creation_input_tokens`: token được ghi vào cache ở request này.
- `cache_read_input_tokens`: token được đọc lại từ cache.

Hai loại token này có giá riêng, khác giá input thường. **Repo chưa có giá cache trong `config/models.yaml`**, nên `estimate_cost_usd` hiện bỏ qua hai trường trên. Khi bạn dùng cache với API thật, con số ước tính sẽ lệch so với hoá đơn. Script in cảnh báo nếu thấy token cache trong `usage`. Mock hiện chưa điền hai trường này.

Điều đã kiểm ở module 07: đổi `effort` hoặc cấu hình thinking giữa các request làm mất cache; thêm chỉ dẫn bằng message `system` giữa hội thoại thì giữ được cache. Giá cache, thời gian sống của cache và cách đánh dấu chỗ cache sẽ ở phần sau, kèm ngày kiểm.

## Bẫy thường gặp

- **Cộng `thinking_tokens` vào `output_tokens`.** Thinking đã nằm trong `output_tokens`; cộng lại là tính hai lần.
- **Gõ giá vào code.** Giá đổi; đọc từ `config/models.yaml`.
- **Coi `estimate_cost_usd` là hoá đơn.** Nó bỏ qua cache, giá prompt dài của Haiku 5.5, giá batch, hệ số `inference_geo`. Hoá đơn thật xem ở Console.
- **Chỉ nhìn một lời gọi.** Nhân với số lượt, số người dùng và số lần retry.
- **Quên rằng input lớn dần** theo độ dài hội thoại, kể cả block thinking của các lượt trước.
- **Đặt `max_tokens` quá sát để tiết kiệm.** Thinking dùng hết trần, text rỗng, bạn vẫn trả tiền phần thinking (module 07, mục 4).

## Điều gì đã thay đổi ở model 5.x

| Trước đây | Bây giờ |
|---|---|
| Thinking tắt mặc định, không tốn gì nếu không bật | Adaptive thinking bật sẵn; token thinking tính là output, kể cả khi text bị ẩn |
| Giới hạn thinking bằng `budget_tokens` | `budget_tokens` trả 400; giảm chi phí bằng `effort`, chặn trần bằng `max_tokens` |
| Thinking của lượt cũ bị bỏ khỏi context | Thinking cũ được giữ lại và tính là input token ở các lượt sau |

## Tiếp theo

Phần sau của module 06: giá cache và cách bật prompt caching, đếm token bằng API, Batch API, message threads. Nguồn: [references.md](references.md).
