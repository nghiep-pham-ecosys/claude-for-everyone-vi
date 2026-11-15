# 04 · RAG: tìm tài liệu rồi trả lời có nguồn

**Loại:** Learn + Build · **Thời lượng:** khoảng 2,5 giờ · **Cần:** module 01–03, nên học 05 trước · **Chi phí:** $0 ở mock mode; dưới $0,01 nếu chạy thật với `claude-haiku-5-5` (giá kiểm 24/10/2026, xem [references.md](references.md)). Bước tìm kiếm chạy hoàn toàn trên máy, không cần API, không cần model embedding.

## Mục tiêu

Sau module này bạn:

- Biết khi nào cần RAG và khi nào chỉ cần đưa cả tài liệu vào prompt.
- Viết được BM25 cho tiếng Việt từ đầu, hiểu vì sao nó tìm tốt mã lỗi, mã thiết bị, con số.
- Chia tài liệu thành đoạn mà không làm mất ngữ cảnh.
- Ghép hai bộ xếp hạng bằng Reciprocal Rank Fusion (RRF).
- Đưa đoạn tìm được cho Claude bằng block `search_result` và đọc trích dẫn `search_result_location`.
- Để Claude tự gọi tool tìm kiếm khi cần.

| Learn | Build |
|---|---|
| Đọc mục 1–7, chạy 5 script trong `python/` | Làm 3 bài trong `exercises/`, chấm bằng test |

## Vì sao học cái này

Claude không biết gì về tài liệu nội bộ của bạn: sổ tay phòng thí nghiệm, hướng dẫn máy, quy định công ty. Muốn Claude trả lời theo tài liệu đó, bạn phải đưa tài liệu vào prompt.

Khi kho tài liệu nhỏ, cách đơn giản nhất là gửi cả kho. Bài blog Contextual Retrieval của Anthropic (2024) gợi ý: kho dưới khoảng 200.000 token thì cứ gửi cả kho, kết hợp prompt caching cho rẻ. Model hiện nay có cửa sổ ngữ cảnh lớn hơn nhiều, nhưng mỗi request vẫn trả tiền cho mọi token gửi đi, và tài liệu càng dài thì càng khó để Claude chú ý đúng chỗ.

RAG (Retrieval-Augmented Generation) làm khác: **tìm** vài đoạn liên quan nhất trước, rồi chỉ gửi những đoạn đó. Chất lượng câu trả lời phụ thuộc phần lớn vào bước tìm. Claude không thể trả lời đúng từ một đoạn không được tìm thấy.

## Tối thiểu chạy được

```bash
CLAUDE_MOCK=1 uv run python modules/04-rag/python/01_bm25.py
```

| Script | Ý chính | Gọi Claude? |
|---|---|---|
| [`01_bm25.py`](python/01_bm25.py) | BM25 trên sổ tay; mã lỗi; câu hỏi gõ không dấu | Không |
| [`02_ngu_canh.py`](python/02_ngu_canh.py) | Thêm tiêu đề/mục vào đầu đoạn: đoạn đúng leo từ hạng 14 lên 4 | Không |
| [`03_ngu_canh_claude.py`](python/03_ngu_canh_claude.py) | Nhờ Claude viết câu ngữ cảnh cho từng đoạn | Có, 4 lời gọi |
| [`04_search_result.py`](python/04_search_result.py) | Tìm hybrid → `search_result` → câu trả lời có nguồn | Có, 1 lời gọi |
| [`05_rag_tool.py`](python/05_rag_tool.py) | Claude tự gọi tool `tim_so_tay` | Có, 2–4 lời gọi |

Kho tài liệu là [`data/so_tay/`](data/so_tay): 7 trang sổ tay **hư cấu** của một phòng thí nghiệm môi trường. Máy MD-300, mã lỗi, mã thiết bị và mọi con số đều bịa.

Script nạp code từ `solutions/`. Đặt `CHAM=exercises` thì script chạy bằng code bạn viết.

Ở mock mode, câu trả lời không hiểu câu hỏi. Mock chọn khối có nhiều từ trùng với câu hỏi nhất để trả về trích dẫn `search_result_location` đúng định dạng. Phần tìm kiếm (BM25, RRF) là code thật, chạy giống hệt khi có key.

## 1. Đường ống RAG

```text
Chuẩn bị (một lần)         tài liệu ──▶ chia đoạn ──▶ thêm ngữ cảnh ──▶ lập chỉ mục BM25
Mỗi câu hỏi                câu hỏi ──▶ tìm top-k ──▶ search_result ──▶ Claude ──▶ trả lời + trích dẫn
```

Mỗi bước có một cách hỏng riêng:

| Bước | Hỏng thế nào |
|---|---|
| Chia đoạn | Đoạn quá ngắn mất ngữ cảnh; quá dài thì loãng, tốn token |
| Lập chỉ mục | Không chuẩn hoá Unicode, chữ có dấu gõ hai kiểu không khớp nhau |
| Tìm | Từ đồng nghĩa ("bao lâu" và "tần suất") không khớp nhau |
| Trả lời | Claude trả lời từ kiến thức chung thay vì đoạn tìm được |

Đo từng bước riêng. Khi câu trả lời sai, việc đầu tiên là xem đoạn đúng có nằm trong top-k không.

## 2. BM25: tìm theo từ khoá

BM25 chấm điểm từng đoạn theo các từ trong câu hỏi, dựa trên ba ý:

1. **Từ hiếm đáng giá hơn từ phổ biến.** "e-17" chỉ có trong một đoạn nên được nhiều điểm; "máy" có ở khắp nơi nên gần như không. Đây là phần `idf`.
2. **Từ lặp lại được cộng thêm, nhưng có trần.** Đoạn nhắc "pH" mười lần không hơn đoạn nhắc hai lần là bao. Tham số `k1` điều khiển độ bão hoà này.
3. **Đoạn dài bị trừ bớt.** Đoạn dài chứa nhiều từ hơn chỉ vì nó dài. Tham số `b` điều khiển mức trừ.

```text
điểm(đoạn) = Σ  idf(w) · f·(k1 + 1) / (f + k1·(1 − b + b·dl/avgdl))
idf(w)     = ln(1 + (N − n + 0,5) / (n + 0,5))
```

Trong đó `f` là số lần từ `w` có trong đoạn, `dl` là độ dài đoạn, `avgdl` là độ dài trung bình, `N` là số đoạn, `n` là số đoạn chứa `w`. Giá trị thường dùng: `k1 = 1,5`, `b = 0,75`.

**Vì sao BM25, khi đã có embedding?** Embedding biến đoạn văn thành vector theo nghĩa, nên tìm được "bao lâu" khi tài liệu ghi "tần suất". Nhưng nó dễ hụt các chuỗi chính xác: mã lỗi `E-17`, mã thiết bị `TB-07`, mã mẫu `SX03-20261012-01`. BM25 khớp đúng những chuỗi đó. Bài blog của Anthropic dùng cả hai và thấy kết hợp tốt hơn chỉ dùng embedding.

Module này chỉ dùng BM25 để mọi thứ chạy trên máy, không cần thêm thư viện hay key nào. Mục 7 nói cách thêm embedding.

### Tách từ tiếng Việt

BM25 chỉ tốt bằng bước tách từ. Ba điều cho tiếng Việt:

- **Chuẩn hoá Unicode (NFC).** Chữ "ệ" có thể được lưu thành một ký tự hoặc thành "e" cộng hai dấu. Hai cách trông giống hệt nhau nhưng không bằng nhau khi so chuỗi. Luôn `unicodedata.normalize("NFC", ...)` trước khi so.
- **Giữ nguyên mã có gạch nối và số thập phân.** Regex `\w+(?:[-.,]\w+)*` giữ `e-17`, `md-300`, `7,00` thành một token. Tách `e-17` thành `e` và `17` thì "e" khớp lung tung.
- **Người dùng hay gõ không dấu.** "hieu chuan" không khớp "hiệu chuẩn". Lập thêm một chỉ mục đã bỏ dấu, rồi hợp nhất hai kết quả bằng RRF (mục 5).

Tiếng Việt viết theo âm tiết: "hiệu chuẩn" là hai token "hiệu" và "chuẩn". BM25 theo âm tiết vẫn chạy tốt cho kho nhỏ. Tách theo từ ghép cần thêm bộ tách từ tiếng Việt; repo không dùng.

## 3. Chia đoạn

Đoạn là đơn vị được tìm và được gửi cho Claude. Cách chia của repo, theo đúng cấu trúc markdown của sổ tay:

- Không bao giờ gom qua ranh giới mục `##`: một đoạn chỉ thuộc một mục.
- Trong một mục, gom các đoạn văn liên tiếp tới khi chạm trần ký tự.
- Không cắt giữa câu. Đoạn văn dài hơn trần thì đứng một mình.

Không có kích thước "đúng". Đoạn nhỏ thì tìm chính xác hơn nhưng dễ mất ngữ cảnh; đoạn lớn thì ngược lại. Đo trên câu hỏi thật.

## 4. Ngữ cảnh cho đoạn

Cắt đoạn làm mất thông tin. Đoạn "Thực hiện lại sau mỗi 8 giờ đo, khi đổi điện cực..." không nhắc "hiệu chuẩn" hay "pH", vì những từ đó nằm ở tiêu đề tài liệu. Câu hỏi "bao lâu phải hiệu chuẩn lại máy đo pH" khó tìm ra nó.

**Cách miễn phí:** chép tiêu đề và tên mục vào đầu đoạn trước khi lập chỉ mục:

```text
Tài liệu: Hiệu chuẩn máy đo pH. Mục: Tần suất.
Thực hiện lại sau mỗi 8 giờ đo, khi đổi điện cực, ...
```

Trên sổ tay mẫu, chỉ thay đổi này đưa đoạn đúng từ hạng 14 lên hạng 4 ([`02_ngu_canh.py`](python/02_ngu_canh.py)).

**Cách tốn tiền hơn: contextual retrieval.** Gửi Claude cả tài liệu cùng một đoạn, xin 1–2 câu đặt đoạn đó vào bối cảnh, rồi ghép câu đó vào đầu đoạn. Bài blog của Anthropic dùng cách này với câu ngữ cảnh khoảng 50–100 token. Trên các tập thử của họ, ngữ cảnh cho cả embedding lẫn BM25 giảm tỉ lệ tìm hụt trong top-20 đoạn từ 5,7% xuống 2,9%, và thêm bước rerank thì xuống 1,9%. Đó là số liệu năm 2024 trên dữ liệu của họ; trên kho của bạn phải tự đo.

Mỗi đoạn một lời gọi, và mỗi lời gọi gửi lại cả tài liệu. Với kho lớn, dùng prompt caching cho phần tài liệu và Batch API (module 06). Đặt `effort` `low` và `max_tokens` nhỏ: đây là việc ngắn làm hàng nghìn lần. [`03_ngu_canh_claude.py`](python/03_ngu_canh_claude.py) chỉ chạy cho một tài liệu để giới hạn chi phí.

## 5. Ghép nhiều bộ tìm kiếm: RRF

Bạn có hai danh sách xếp hạng, ví dụ BM25 có dấu và BM25 không dấu, hoặc BM25 và embedding. Điểm của chúng không cùng thang, nên không cộng thẳng được. **Reciprocal Rank Fusion** chỉ dùng thứ hạng:

```text
điểm_RRF(đoạn) = Σ trên các danh sách  1 / (k + hạng của đoạn trong danh sách đó)
```

Thường đặt `k = 60`. Đoạn đứng cao ở cả hai danh sách được nhiều điểm nhất; đoạn chỉ xuất hiện ở một danh sách vẫn có cơ hội. `rag_mau.tim()` ghép BM25 có dấu với BM25 không dấu theo cách này, nên câu hỏi gõ có dấu hay không dấu đều tìm được.

## 6. Đưa kết quả cho Claude: `search_result`

Bạn có thể dán đoạn tìm được vào prompt dưới dạng text. Cách tốt hơn là block `search_result`:

```python
{"type": "search_result",
 "source": "kb://so-tay/02_ma_loi_md300#2",       # mã ổn định của đoạn: URL hoặc mã nội bộ
 "title": "Mã lỗi máy đo đa chỉ tiêu MD-300 — Lỗi điện cực",
 "content": [{"type": "text", "text": "E-17: điện cực khô ..."},
             {"type": "text", "text": "E-18: điện cực không phản hồi ..."}],
 "citations": {"enabled": True}}
```

Bật citations thì mỗi khẳng định trong câu trả lời trỏ về khối text đã dùng:

```text
citation: type="search_result_location", source="kb://so-tay/02_ma_loi_md300#2",
          search_result_index=0, start_block_index=0, end_block_index=1, cited_text="E-17: ..."
```

Luật cần nhớ (docs Search results; `claude_vi` chặn trước):

- Bắt buộc có `source`, `title`, `content`. `content` chỉ gồm block text có chữ, không có ảnh.
- Claude trích **nguyên khối** text, không trích một phần khối. Muốn trích dẫn sát hơn thì chia `content` nhỏ hơn: repo cho mỗi dòng một khối.
- `search_result_index` đếm từ 0 trên mọi block `search_result` của request, theo thứ tự xuất hiện, kể cả trong `tool_result`.
- Citations bật cho tất cả hoặc không cái nào.
- `search_result` chỉ nằm trong lượt user (kể cả trong `tool_result`), không nằm trong lượt assistant.
- `cited_text` không tính vào output token.
- Đừng viết "chỉ trả JSON" khi muốn có trích dẫn: request chạy nhưng có thể gần như không có trích dẫn nào (module 05).

So với block `document` của module 05: `document` dành cho một tài liệu nguyên vẹn (PDF, văn bản), API tự cắt câu. `search_result` dành cho các đoạn bạn đã tìm, với `source` và `title` do bạn đặt. Đó là thứ bạn cần để hiển thị link "xem nguồn".

Trong `system`, nói rõ Claude chỉ trả lời dựa trên kết quả tìm kiếm và nói "không có thông tin" khi không tìm thấy, kèm lý do. [`04_search_result.py`](python/04_search_result.py) làm đúng điều này.

### Để Claude tự tìm

Script 04 luôn tìm trước rồi mới hỏi. [`05_rag_tool.py`](python/05_rag_tool.py) đưa việc tìm thành một tool. Claude quyết định có cần tìm không, chọn từ khoá, và tìm thêm nếu chưa đủ. Tool trả về danh sách `search_result` trong `tool_result`:

- Nếu `tool_result` có một `search_result` thì mọi block bên trong phải là `search_result`. Muốn kèm ghi chú thì đặt nó vào `content` của một `search_result`.
- Không tìm thấy gì thì trả một block text "Không tìm thấy đoạn nào." thay vì ném lỗi, để Claude giải thích cho người dùng.
- Giữ `tool_choice` là `auto`. Docs Search results có ví dụ ép gọi tool bằng `tool_choice`, nhưng `any`/`tool` trả 400 trên Opus 5.5, Sonnet 5.5 và Fable 5.x. Muốn chắc Claude tìm thì dùng script 04: tìm trước bằng code.

## 7. Mở rộng: thêm embedding chạy local

BM25 không hiểu đồng nghĩa: "bao lâu" không khớp "tần suất". Một model embedding chạy trên máy sẽ bù được chỗ này. Cách ghép vào code của module:

1. Cài một thư viện embedding và một model đa ngôn ngữ có hỗ trợ tiếng Việt (tải về một lần, chạy offline sau đó).
2. Mã hoá mọi đoạn (đã thêm ngữ cảnh) thành vector một lần, lưu lại.
3. Mỗi câu hỏi: mã hoá câu hỏi, lấy top-20 đoạn theo cosine similarity.
4. Hợp nhất danh sách đó với danh sách BM25 bằng `hop_nhat_rrf` của bài 3. Phần còn lại giữ nguyên.

Repo **không** cài sẵn phần này, vì thư viện embedding thường kéo theo PyTorch (hàng trăm MB) và CI phải tải model. Trước khi thêm vào dự án thật, đo xem nó có giúp trên câu hỏi của bạn không: với kho toàn mã và thuật ngữ, BM25 + ngữ cảnh có thể đã đủ.

Anthropic không có API embedding riêng. Docs Embeddings giới thiệu nhà cung cấp bên ngoài; dùng họ thì cần thêm một loại key.

## Bẫy thường gặp

- **Dựng RAG khi kho đủ nhỏ để gửi cả.** Đo chi phí hai cách trước.
- **Không chuẩn hoá Unicode.** Hai cách gõ "ệ" không khớp nhau, kết quả tìm kiếm thất thường.
- **Tách `E-17` thành `e` và `17`.**
- **Bỏ qua người dùng gõ không dấu.**
- **Cắt đoạn giữa câu, hoặc gom qua ranh giới mục.**
- **Đoạn mất ngữ cảnh** ("thực hiện lại sau mỗi 8 giờ" mà không biết thực hiện cái gì).
- **Cộng thẳng điểm BM25 với điểm embedding.** Khác thang điểm. Dùng RRF.
- **Lấy quá ít đoạn.** Đoạn đúng ở hạng 4 mà chỉ gửi top-3 thì Claude không thấy. Bài blog thấy top-20 tốt hơn top-5 và top-10 trên dữ liệu của họ.
- **Dán đoạn vào prompt bằng text thường** rồi xin Claude tự ghi nguồn. Dùng `search_result` + citations.
- **`search_result` trộn với text trong cùng một `tool_result`** → 400.
- **Ép gọi tool tìm kiếm bằng `tool_choice` `any`** → 400 trên nhiều model 5.x.
- **Không có câu "không có thông tin thì nói không có"** trong `system`. Claude sẽ lấp chỗ trống bằng kiến thức chung.
- **Đặt nội dung tìm được vào message `system`.** Đó là dữ liệu bên ngoài, không phải chỉ dẫn (module 07).

## Điều gì đã thay đổi ở model 5.x

| Trước đây | Bây giờ |
|---|---|
| Dán đoạn vào prompt, xin model ghi "[nguồn 2]" | Block `search_result` + citations: API trả `source` và vị trí khối, `cited_text` không tốn output token |
| Ép gọi tool tìm kiếm bằng `tool_choice` `any` | 400 trên Opus 5.5, Sonnet 5.5, Fable 5.x; tìm trước bằng code hoặc để `auto` |
| Prefill "Theo tài liệu," để ép Claude bám tài liệu | Prefill trả 400; nói rõ trong `system` |
| Ngữ cảnh đoạn sinh bằng Claude 3 Haiku (bài blog 2024) | Haiku 5.5 với effort `low`; Claude 3 Haiku đã retired 20/4/2026 |

## Bài tập

```bash
CHAM=exercises uv run pytest modules/04-rag -q
```

| Bài | Nội dung |
|---|---|
| [`bai1_bm25.py`](exercises/bai1_bm25.py) | Tách từ tiếng Việt (NFC, bỏ dấu, giữ mã), BM25 đúng công thức |
| [`bai2_chia_doan.py`](exercises/bai2_chia_doan.py) | Chia đoạn theo mục, thêm tiêu đề/mục, request xin Claude viết ngữ cảnh |
| [`bai3_hop_nhat.py`](exercises/bai3_hop_nhat.py) | RRF, đóng gói `search_result`, đọc `search_result_location` |

Làm xong cả ba thì chạy lại các script với `CHAM=exercises` để thấy cả đường ống chạy bằng code của bạn. Lời giải trong [`solutions/`](solutions/). Tự kiểm tra: [quiz.md](quiz.md). Nguồn: [references.md](references.md).

## Tiếp theo

Module 05 — Structured outputs, PDF và Citations. Đã học 05 rồi thì sang module 06 — Chi phí, nơi prompt caching làm bước contextual retrieval rẻ đi nhiều.
