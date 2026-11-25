# 06 · Chi phí

**Loại:** Learn + Build · **Thời lượng:** khoảng 2 giờ · **Cần:** module 01 (mục 5) và 07 (mục 4) · **Chi phí:** $0 ở mock mode; dưới $0,02 nếu chạy thật với `claude-haiku-5-5` (giá kiểm 25/11/2026 trong [`config/models.yaml`](../../config/models.yaml), xem [references.md](references.md))

## Mục tiêu

Sau module này bạn:

- Biết một lời gọi bị tính tiền theo những con số nào trong `msg.usage`.
- Đọc giá từ `config/models.yaml` thay vì gõ số vào code.
- Tính được **trần chi phí** của một lời gọi **trước khi** gửi, với input đếm bằng `count_tokens`.
- Bật **prompt caching** đúng chỗ và tính đúng giá ghi cache, đọc cache.
- Gửi việc không gấp qua **Batch API** với nửa giá, và ghép kết quả bằng `custom_id`.
- Biết **message threads** (beta) làm gì cho request, và vì sao nó không thay được cache.

| Learn | Build |
|---|---|
| Đọc mục 1–9, chạy 5 script trong `python/` | Làm 3 bài trong `exercises/`, chấm bằng test |

## Vì sao học cái này

Chi phí của một ứng dụng Claude không nằm ở một lời gọi. Nó nằm ở lời gọi đó nhân với số người dùng, số lượt hội thoại và số lần retry. Một con số nhỏ như $0,0005 thành đáng kể khi nhân lên hàng triệu.

Bạn cần hai thói quen. Trước khi gọi: biết lời gọi này **tốn tối đa** bao nhiêu. Sau khi gọi: biết nó **đã tốn** bao nhiêu và vì sao. Rồi ba công cụ để trả ít hơn cho cùng một việc: cache phần prompt lặp lại, gom việc không gấp vào batch, và giữ request nhỏ khi hội thoại dài.

## Tối thiểu chạy được

```bash
CLAUDE_MOCK=1 uv run python modules/06-cost/python/01_uoc_tinh_chi_phi.py
```

| Script | Ý chính |
|---|---|
| [`01_uoc_tinh_chi_phi.py`](python/01_uoc_tinh_chi_phi.py) | Bảng giá từ config, trần output theo `max_tokens`, tách chi phí từ `usage` |
| [`02_prompt_caching.py`](python/02_prompt_caching.py) | Ghi cache một lần, đọc nhiều lần; breakpoint sai chỗ; đổi effort mất cache; prompt quá ngắn; hoà vốn |
| [`03_dem_token.py`](python/03_dem_token.py) | `count_tokens` trước khi gọi, chặn request vượt ngân sách, so số đếm với `usage` |
| [`04_batch.py`](python/04_batch.py) | Tạo batch, chờ `ended`, ghép kết quả bằng `custom_id`, so giá batch với giá thường |
| [`05_message_threads.py`](python/05_message_threads.py) | Thread create/continue, gửi lại cả hội thoại khi gặp 404, thread có và không có cache |

Script không cần API key và không gọi mạng. Mock trả `usage` giả lập: số token input đếm theo quy ước **1 token ≈ 4 ký tự**, số token thinking đổi theo `effort`. Đó là số của mock, không phải số thật. **Giá** thì là giá thật, đọc từ config. Sổ tay dùng làm prompt dài ở [`data/so_tay_thiet_bi.md`](data/so_tay_thiet_bi.md) là dữ liệu hư cấu.

## 1. Bạn trả tiền cho những gì

`msg.usage` có ba con số chính (module 01, mục 5):

- `input_tokens`: mọi thứ bạn gửi, gồm `system` và toàn bộ lịch sử hội thoại (khi không dùng prompt caching; có cache thì xem mục 5).
- `output_tokens`: mọi thứ Claude sinh ra, **gồm cả thinking**, kể cả khi text thinking bị ẩn.
- `output_tokens_details.thinking_tokens`: phần thinking nằm trong `output_tokens`. Đừng cộng nó thêm lần nữa.

Công thức khi không có cache, giá tính theo triệu token (MTok):

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

Phần 1 của script in bảng giá các model `active` trong config. Lưu ý từ chính config: giá `price_per_mtok` của `claude-haiku-5-5` là giá cho prompt tới 100.000 token; prompt dài hơn có giá cao hơn, ghi ở `long_context` (mục 5).

## 3. Ước tính trước khi gọi

`max_tokens` là trần **cứng** cho mọi token output của một lời gọi: thinking + text (module 07, mục 4). Nên trước khi gửi, bạn đã biết:

```text
chi phí output tối đa = max_tokens × giá output / 1.000.000
```

Đó là việc của `tran_chi_phi_output(model, max_tokens)` trong script. Với `MAX_TOKENS=1024` mặc định của repo, bảng ở phần 1 của script cho thấy trần này khác nhau rất xa giữa các model.

Phần input khó hơn: bạn chưa biết số token trước khi gửi. Có hai cách:

- **Đo một lần, dùng lại:** gọi một request giống hệt (hoặc chạy mock với fixture ghi từ API thật) rồi đọc `input_tokens`.
- **Đếm token bằng API:** `client.count_tokens(...)` (mục 6).

Ước tính trước khi gọi dùng để **chặn**, không để báo cáo. Ví dụ: từ chối một job nếu trần chi phí của cả loạt request vượt ngân sách.

## 4. Đọc chi phí sau khi gọi

`tach_chi_phi(msg)` trong script trả về:

| Khoá | Nghĩa |
|---|---|
| `input` | `input_tokens × giá input` |
| `output` | `output_tokens × giá output` (đã gồm thinking) |
| `thinking` | phần của `output` do thinking, chỉ để xem, không cộng thêm |
| `tong` | `input + output`; khi không có cache (và prompt dưới ngưỡng `long_context`) thì bằng `estimate_cost_usd(msg)` |
| `token_cache` | số token ghi + đọc cache; giá riêng, tách ở mục 5 |

Phần 3 của script gọi cùng một câu hỏi với effort `low` và `high`. Input không đổi; output và phần thinking đổi theo effort. Muốn giảm chi phí trên cả loạt request thì hạ effort; muốn chắc chắn không vượt một mức thì đặt `max_tokens` (module 07, mục 4).

## 5. Prompt caching

**Prompt caching** (lưu đệm prompt): nhiều request bắt đầu bằng cùng một phần dài (danh sách tool, system prompt, tài liệu). API lưu phần đầu đó lại. Request sau đọc lại phần đã lưu thay vì xử lý lại từ đầu. Bạn trả **nhiều hơn** một chút ở lần ghi và **ít hơn hẳn** ở mỗi lần đọc.

### Đánh dấu chỗ cache

Đặt `cache_control` lên block **cuối cùng của phần không đổi**. Phần đó và mọi thứ trước nó là prefix được cache:

```python
system = [
    {"type": "text", "text": "Bạn là trợ lý của phòng thí nghiệm."},
    {"type": "text", "text": SO_TAY, "cache_control": {"type": "ephemeral"}},   # breakpoint
]
client.create(system=system, messages=[{"role": "user", "content": cau_hoi}])
```

- Prefix đi theo thứ tự **tools → system → messages**. Đổi một chỗ thì cache của chỗ đó và mọi phần sau nó mất.
- Tối đa **4 breakpoint** mỗi request. `claude_vi.rules` chặn trước khi gửi.
- `ttl` (thời gian sống): `"5m"` (mặc định) hoặc `"1h"`. Mỗi lần đọc trúng thì cache được làm mới, không tốn thêm. Nếu dùng cả hai, breakpoint `1h` phải đứng trước breakpoint `5m`.
- Prompt ngắn hơn ngưỡng thì **không được cache và không báo lỗi**. Ngưỡng của 5 model active là 512 token (`cache_min_tokens` trong config). Cả hai trường cache trong `usage` khi đó bằng 0.
- **Automatic caching:** một trường `cache_control` ở cấp cao nhất của request. API tự đặt breakpoint lên block cuối cùng cache được của `messages` (block cuối không hợp lệ thì lùi về block gần nhất) và dời theo khi hội thoại dài ra. Nó chiếm một trong 4 chỗ breakpoint. Nếu block cuối đổi mỗi lần (giờ hiện tại, chỗ trống điền sau), dùng breakpoint tự đặt ở cuối phần không đổi thay vì automatic caching.

### Đọc `usage` khi có cache

```text
tổng input = cache_read_input_tokens + cache_creation_input_tokens + input_tokens
```

- `cache_creation_input_tokens`: token **ghi** vào cache ở request này. `usage.cache_creation` tách thành `ephemeral_5m_input_tokens` và `ephemeral_1h_input_tokens`.
- `cache_read_input_tokens`: token **đọc** từ cache.
- `input_tokens`: chỉ phần **sau** breakpoint cuối, tính giá input thường.

`tach_input(msg)` trong script 02 trả về bốn phần này. Phần 3 của script cho thấy lần 1 ghi, lần 2 và 3 đọc.

### Giá

Giá nằm ở `cache_price_per_mtok` trong config, kiểm trên trang Pricing ngày 25/11/2026:

| Loại token | So với giá input |
|---|---|
| Ghi cache 5 phút | 1,25x |
| Ghi cache 1 giờ | 2x |
| Đọc cache | 0,1x ở Haiku 5.5 và các model cũ hơn; **0,05x** ở Opus 5.5 và Sonnet 5.5; **0,025x** ở Fable 5.2 và 5.1 |

Hệ quả, theo trang Pricing: cache 5 phút hoà vốn sau **1 lần đọc**, cache 1 giờ sau **2 lần đọc**. Phần 6 của script 02 tính lại điều này cho từng model bằng giá trong config. Bài 1 bắt bạn tự viết.

`estimate_cost_usd(msg)` giờ tính cả ghi cache 5 phút, ghi cache 1 giờ và đọc cache. Với Haiku 5.5, prompt trên 100.000 token (tính cả token đọc và ghi cache) trả giá cao hơn cho **mọi** loại token; config ghi giá này ở `long_context` và `estimate_cost_usd` dùng nó.

### Cái gì làm mất cache

- Sửa tool, system hoặc một message cũ: mất từ chỗ sửa trở đi.
- Đổi cấu hình thinking: luôn mất phần messages, trên một số model mất cả tools và system.
- Đổi `effort`: **có thể** mất phần messages, trên một số model cả tools và system. Đặt `effort` bằng đúng giá trị mặc định thì không mất. Phần 4 của script 02 cho thấy điều này; mock coi như mất cả prefix.
- Đặt breakpoint lên block **thay đổi mỗi lần** (giờ hiện tại, câu hỏi của người dùng): lần nào cũng ghi cả prefix, không bao giờ đọc. Phần 2 của script 02 là ví dụ.
- Không dùng tới quá TTL. Không có cách xoá cache bằng tay.
- Gửi nhiều request song song ngay lúc đầu: cache chỉ dùng được sau khi response đầu tiên bắt đầu, nên các request song song đều ghi. Chờ request đầu xong rồi mới gửi phần còn lại.

Thêm chỉ dẫn bằng message `system` giữa hội thoại thì giữ được cache (module 07, mục 7).

## 6. Đếm token trước khi gọi

`client.count_tokens(...)` gọi `POST /v1/messages/count_tokens`. Nó nhận gần như cùng tham số với `create` (`system`, `tools`, `messages`, `thinking`, ảnh, PDF) nhưng **không** có `max_tokens`. Nó trả `MessageTokensCount` với một trường `input_tokens`.

```python
n = client.count_tokens(system=SO_TAY, messages=hoi).input_tokens
toi_da = (n * gia["input"] + max_tokens * gia["output"]) / 1_000_000
```

Điều cần biết (docs Token counting, kiểm 25/11/2026):

- **Miễn phí**, nhưng có giới hạn số request mỗi phút riêng, tách khỏi giới hạn của Messages API.
- Số đếm là **ước tính**, có thể lệch chút ít so với `usage` thật. Token do hệ thống thêm có thể được đếm nhưng không bị tính tiền.
- **Không dùng cache.** Nhận `cache_control` nhưng chỉ `create` mới ghi và đọc cache. Số đếm là tổng input, chưa trừ phần sẽ đọc từ cache.
- Luật 400 của model vẫn áp dụng. Ví dụ: Opus 5.5, Sonnet 5.5 và Fable 5.2 từ chối `tool_choice` any/tool ngay cả khi đếm token.
- Mỗi model đếm bằng tokenizer của nó. Từ model 4.7 trở đi, cùng một đoạn text cho khoảng 30% token nhiều hơn so với model cũ (tới khoảng 35% với Opus 5.5, tuỳ nội dung). Đếm lại bằng đúng model sẽ dùng.
- Một số input `create` nhận nhưng `count_tokens` trả lỗi: server tool (trừ advisor tool), MCP connector, ảnh/PDF gửi bằng `url` hoặc `file` (Files API). Ảnh và PDF phải gửi base64.

Dùng `count_tokens` để **chặn**: phần 2 của script 03 chỉ gửi request khi trần nằm trong ngân sách. Bài 2 bắt bạn viết hàm đó.

## 7. Batch API: nửa giá cho việc không gấp

**Message Batches API**: gửi một lô request, API xử lý bất đồng bộ, bạn lấy kết quả sau. Đổi lại, mọi token input và output trả **50%** giá chuẩn (`batch_price_multiplier: 0.5` trong config).

```python
batch = client.batch_create([
    {"custom_id": "cau-000", "params": {"messages": [{"role": "user", "content": "..."}]}},
    ...
])
while client.batch_retrieve(batch.id).processing_status != "ended":
    time.sleep(30)
for r in client.batch_results(batch.id):
    if r.result.type == "succeeded":
        usd = estimate_cost_usd(r.result.message, batch=True)
```

Luật chính (docs Batch processing, kiểm 25/11/2026):

| Điều | Giá trị |
|---|---|
| Kích thước | tối đa 100.000 request hoặc 256 MB mỗi batch |
| Thời gian | đa số xong trong 1 giờ; quá 24 giờ chưa xong thì request còn lại `expired` |
| Kết quả | file `.jsonl` ở `results_url`, giữ 29 ngày kể từ lúc tạo batch |
| `custom_id` | 1–64 ký tự chữ, số, `-`, `_`; không trùng trong batch |
| `processing_status` | `in_progress` → `ended` (hoặc `canceling` → `ended` khi huỷ) |
| Kết quả từng request | `succeeded` (tính tiền), `errored`, `canceled`, `expired` (không tính tiền) |

Ba điều dễ sai:

- **Thứ tự kết quả không theo thứ tự gửi.** Ghép bằng `custom_id`. Mock cố ý trả ngược để bạn thấy.
- **`params` được kiểm sau.** Request sai chỉ hiện `errored` khi cả batch đã xong. `client.batch_create` kiểm luật từng request **trước** khi gửi để bạn không chờ hàng giờ mới biết sai.
- **Không dùng được trong batch:** `stream: true`, fast mode (`speed`), `fallbacks`, `max_tokens: 0`, message threads.

Batch cộng dồn được với prompt caching: cả hai giảm giá nhân với nhau. Nhưng cache trong batch chỉ là "best-effort" (docs ghi tỉ lệ trúng thường từ 30% tới 98%), vì các request chạy song song và không theo thứ tự. Docs khuyên dùng cache 1 giờ, gửi trước một request để ghi cache, xong rồi mới gửi batch. Mock xử lý tuần tự nên luôn trúng; đừng lấy con số của mock làm kỳ vọng.

## 8. Message threads (beta)

**Message threads** (ra mắt dạng beta ngày 02/11/2026, header `anthropic-beta: message-threads-2026-08-12`): API giữ hội thoại trên server một thời gian ngắn. Lượt đầu gửi đầy đủ như thường kèm `"thread": {"type": "create"}`. Các lượt sau chỉ gửi **message mới** kèm `{"type": "continue", "previous_message_id": <id response trước>}`, không gửi lại `system` và `tools`.

Nó giúp gì: request nhỏ hơn, time to first token thấp và ổn định hơn khi hội thoại dài, nhất là vòng lặp agent. **Nó không làm rẻ hơn.** Docs viết: "Threads do not change pricing or rate limits." Thread **không tự bật cache**. Muốn rẻ hơn, gửi cùng một `cache_control` cấp cao nhất ở **mọi** request của thread. Mỗi lượt khi đó đọc phần cũ từ cache và ghi lượt mới. Phần 1 và 2 của script 05 so hai cách.

Luật chính (docs Message threads, kiểm 25/11/2026):

- Các trường cố định phải **giữ nguyên** suốt thread: `model`, `tool_choice`, `thinking`, `mcp_servers`, `context_management`, `output_config`, `skills` trong `container`, `cache_control` cấp cao nhất, tập beta header (và có hay không có `fallbacks`). Khác thì 400 `thread_fingerprint_mismatch`.
- `system` và `tools` chỉ gửi ở request create. Gửi ở request continue, kể cả giá trị `null`, thì 400.
- Mỗi request có `thread` tối đa 4 breakpoint. Breakpoint trên `system`/`tools` của request create tính lại ở mỗi lượt continue; `cache_control` cấp cao nhất tính một. Thừa thì 400 `thread_unsupported_request`.
- Thread chỉ nối thêm. Mỗi `id` response chỉ continue được **một lần** (lần hai: 400 `thread_already_continued`).
- Thread là **best-effort**. Nó hết hạn 5 phút sau request cuối (mỗi response được lưu tính lại 5 phút). Continue cũng có thể nhận **404 `thread_not_found`** sớm hơn vì lý do khác: response trước chưa xong hoặc không được lưu, model fallback đã trả lời, request đến từ workspace hay key khác. Ứng dụng phải giữ bản sao cả hội thoại và gửi lại bằng một request create mới. Lớp `HoiThoaiThread` trong script 05 làm việc này khi mã lỗi là `thread_not_found` (404 khác, ví dụ model không tồn tại, thì báo lỗi lên); phần 3 giả lập thread hết hạn.
- Không dùng chung được với Batch API và `count_tokens`. Muốn đếm token thì đếm cả hội thoại.
- Không đủ điều kiện ZDR (zero data retention).

Hai giới hạn của repo:

- SDK `anthropic` 1.17.0 đã cài chưa có tham số `thread`, nên `claude_vi` gửi nó qua `extra_body` cùng beta header. Docs mô tả SDK helper `client.beta.messages.thread(...)`; repo chưa kiểm bản SDK nào có helper này.
- Docs không nói rõ phần hội thoại cũ được tính tiền thế nào khi continue. Mock giả định nó vẫn tính là input như khi gửi lại (vì docs nói giá không đổi). Đây là **suy luận của repo**; chỉ số đo khi chạy thật mới là căn cứ.

## 9. Chọn công cụ nào

| Tình huống | Công cụ |
|---|---|
| Cùng một tài liệu hoặc system dài cho nhiều câu hỏi | Prompt caching, breakpoint cuối phần không đổi |
| Hội thoại nhiều lượt | Automatic caching (`cache_control` cấp cao nhất); thêm message threads nếu cần request nhỏ |
| Hàng trăm việc không cần trả lời ngay | Batch API, cộng cache 1 giờ nếu có prefix chung |
| Cần chắc không vượt ngân sách | `count_tokens` + `max_tokens` để tính trần trước khi gửi |
| Muốn mỗi lời gọi tốn ít output hơn | Hạ `effort` (module 07) |

## Bẫy thường gặp

- **Cộng `thinking_tokens` vào `output_tokens`.** Thinking đã nằm trong `output_tokens`; cộng lại là tính hai lần.
- **Gõ giá vào code.** Giá đổi; đọc từ `config/models.yaml`.
- **Coi `estimate_cost_usd` là hoá đơn.** Nó chưa tính hệ số `inference_geo` (1,1x khi chọn chạy ở Mỹ), fast mode, server tool. Hoá đơn thật xem ở Console.
- **Tính token đọc cache theo giá input.** Đọc cache có giá riêng, rẻ hơn nhiều; ghi cache thì đắt hơn input.
- **Breakpoint đặt trên phần thay đổi mỗi lần.** Trả tiền ghi cache mãi mà không bao giờ đọc.
- **Prompt dưới ngưỡng cache.** Không lỗi, không cache; kiểm `cache_creation_input_tokens` sau lần gọi đầu.
- **Đổi effort giữa các request** dùng chung cache. Mỗi lần đổi có thể buộc ghi cache lại.
- **Ghép kết quả batch theo thứ tự.** Dùng `custom_id`.
- **Nghĩ message threads làm rẻ hơn.** Thread làm request nhỏ hơn; cache mới làm rẻ hơn.
- **Dùng số đếm của model cũ cho model mới.** Tokenizer khác nhau; đếm lại.
- **Chỉ nhìn một lời gọi.** Nhân với số lượt, số người dùng và số lần retry.
- **Đặt `max_tokens` quá sát để tiết kiệm.** Thinking dùng hết trần, text rỗng, bạn vẫn trả tiền phần thinking (module 07, mục 4).

## Điều gì đã thay đổi ở model 5.x

| Trước đây | Bây giờ |
|---|---|
| Thinking tắt mặc định, không tốn gì nếu không bật | Adaptive thinking bật sẵn; token thinking tính là output, kể cả khi text bị ẩn |
| Giới hạn thinking bằng `budget_tokens` | `budget_tokens` trả 400; giảm chi phí bằng `effort`, chặn trần bằng `max_tokens` |
| Thinking của lượt cũ bị bỏ khỏi context | Thinking cũ được giữ lại và tính là input token ở các lượt sau |
| Đọc cache 0,1x giá input (vẫn vậy ở Haiku 5.5 và model cũ hơn) | 0,05x ở Opus 5.5 và Sonnet 5.5, 0,025x ở Fable 5.1 và 5.2 |
| Ngưỡng cache 1.024 tới 4.096 token ở model 4.x và Sonnet 5 | 512 token ở cả 5 model active |
| Số token đếm ở model cũ | Tokenizer mới (từ 4.7): khoảng 30% token nhiều hơn cho cùng text |
| Mỗi lượt gửi lại cả hội thoại | Có thêm message threads (beta): chỉ gửi message mới, giá không đổi |

## Bài tập

| Bài | Việc | Chấm |
|---|---|---|
| [`bai1_chi_phi_cache.py`](exercises/bai1_chi_phi_cache.py) | Tách chi phí input, ghi 5 phút, ghi 1 giờ, đọc cache, output; giá batch; số lần đọc để hoà vốn | khớp `estimate_cost_usd`, hoà vốn 1 và 2 lần như docs |
| [`bai2_ngan_sach.py`](exercises/bai2_ngan_sach.py) | Đếm token, tính trần, chỉ gửi khi trong ngân sách | vượt ngân sách thì không gọi `create`; chỉ đếm một lần |
| [`bai3_batch.py`](exercises/bai3_batch.py) | Dựng request với `custom_id` hợp lệ, gom kết quả theo `custom_id` | thứ tự bất kỳ; chỉ `succeeded` tính tiền |

```bash
CHAM=exercises CLAUDE_MOCK=1 uv run pytest modules/06-cost -q   # chấm bài của bạn
CLAUDE_MOCK=1 uv run pytest modules/06-cost -q                  # chấm lời giải
```

Câu hỏi ôn tập: [quiz.md](quiz.md).

## Tiếp theo

Module 08 (agents và workflows) dùng các thói quen ở đây: trần chi phí cho cả vòng lặp agent, đọc `usage` từng lượt. Nguồn của module này: [references.md](references.md).
