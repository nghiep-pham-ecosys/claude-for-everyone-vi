# Đề cương module 08 · Agents và workflows

> **Trạng thái (2026-11-18):** Nghiệp đã duyệt; module đã viết ở [`modules/08-agents-workflows/`](../modules/08-agents-workflows/README.md) (issue #20). Câu hỏi 3–5: giữ tám script, tên thư mục như trên, không có capstone riêng (một capstone agent sau module 10). Đề cương giữ lại làm hồ sơ.

**Loại:** Learn + Build · **Thời lượng dự kiến:** khoảng 3 giờ · **Cần:** module 01–03 và 07; nên học 05 (structured outputs) và 06 (chi phí) · **Chi phí:** $0 ở mock mode. Chi phí chạy thật tính khi viết module, bằng giá trong [`config/models.yaml`](../config/models.yaml), ghi ngày kiểm trong `references.md`.

## Phạm vi

- **Trong module:** ghép nhiều lời gọi thành workflow; vòng lặp agent tự viết bằng `claude_vi`; điều kiện dừng; duyệt tool có tác dụng phụ; ghi trace; chi phí của cả lần chạy.
- **Ngoài module:** Agent SDK (09), MCP (10), Claude Code (11), Agent Skills (12), evals bài bản (13), vận hành production (14). Tool runner của Python SDK chỉ nhắc lại như module 03, mục 3.

Vì sao dạy viết tay trước: module 09 dùng Agent SDK, vốn che đi vòng lặp. Học viên cần thấy vòng lặp, điều kiện dừng và luật lịch sử trước khi giao chúng cho một thư viện.

## Mục tiêu

Sau module này bạn:

- Phân biệt **workflow** (code định sẵn đường đi) với **agent** (Claude tự chọn bước tiếp theo), và chọn cách đơn giản nhất đủ dùng.
- Viết được các mẫu workflow: prompt chaining có cổng kiểm, routing, chạy song song, orchestrator-workers, evaluator-optimizer.
- Viết được một vòng lặp agent có đủ điều kiện dừng: `stop_reason`, số lượt tối đa, trần chi phí.
- Giữ lịch sử agent append-only và chỉnh hướng giữa chừng bằng message `system`, không làm hỏng block thinking.
- Chặn tool có tác dụng phụ bằng một bước duyệt, và coi kết quả tool là dữ liệu không đáng tin.
- Ghi trace từng bước và tính chi phí của cả lần chạy.

## Kịch bản xuyên suốt

Một **trợ lý phòng thí nghiệm hư cấu**. Nó trả lời câu hỏi về quy trình đo, đọc số liệu cảm biến bịa và ghi nhật ký đo.

- Dùng lại dữ liệu đã có: sổ tay PTN hư cấu của module 04 (`modules/04-rag/data/so_tay/`) và hai tool mẫu AQI, nhiệt độ của module 03 (`tools_mau.py`).
- Thêm một tool **có tác dụng phụ**: `ghi_nhat_ky` (ghi một dòng vào file nhật ký tạm). Tool này cần duyệt trước khi chạy.
- Dữ liệu mới (nếu có) đều bịa và ghi ở `NOTICE.md`.
- Đề bài chỉ về đo lường, môi trường, vật liệu. Không có tổng hợp chất nguy hiểm (CLAUDE.md, luật 7).

## Bài học

| # | Bài | Ý chính | Script dự kiến | Dựa trên |
|---|---|---|---|---|
| 1 | Workflow hay agent | Một lời gọi → workflow → agent: khi nào cần bước tiếp theo | `01_mot_loi_goi.py` | 01, 02 mục 7 |
| 2 | Prompt chaining có cổng kiểm | Mỗi bước một việc; code kiểm giữa các bước, sai thì dừng | `02_chuoi_co_cong.py` | 02, 05 |
| 3 | Routing và chạy song song | Phân loại rồi chuyển việc; chia phần và bỏ phiếu chạy đồng thời | `03_dinh_tuyen.py`, `04_song_song.py` | 01 mục 7, 05 |
| 4 | Orchestrator-workers và evaluator-optimizer | Claude lập danh sách việc con; một lượt chấm, một lượt sửa, có trần số vòng | `05_dieu_phoi.py`, `06_danh_gia_sua.py` | 05, 06 |
| 5 | Vòng lặp agent | Từ vòng tool của module 03 tới agent: điều kiện dừng, append-only, nhắc giữa chừng | `07_vong_lap_agent.py` | 03, 06, 07 |
| 6 | An toàn và quan sát | Duyệt tool có tác dụng phụ, nội dung tool không đáng tin, trace, chi phí cả lần chạy | `08_duyet_va_trace.py` | 03 mục 6, 06 |

### 1. Workflow hay agent

- Ba nấc: **một lời gọi** (có RAG và tool nếu cần) → **workflow** (nhiều lời gọi, đường đi do code quyết) → **agent** (Claude quyết bước tiếp theo trong một vòng lặp).
- Agent đổi sự linh hoạt lấy độ trễ, chi phí và khó kiểm. Bắt đầu từ nấc thấp nhất; chỉ lên nấc khi đo được là cần.
- Script chạy cùng một việc theo hai cách (một lời gọi, chuỗi hai bước), in số lời gọi, token và chi phí của mỗi cách.

### 2. Prompt chaining có cổng kiểm

- Module 02 mục 7 đã giới thiệu chuỗi. Bài này thêm **cổng kiểm** (gate): code kiểm đầu ra của bước trước trước khi gọi bước sau.
- Cổng kiểm bằng code, không bằng một lời gọi Claude nữa: đúng schema (structured outputs, module 05), giá trị trong khoảng hợp lệ, trích dẫn có thật.
- Cổng trượt thì dừng chuỗi với lý do rõ ràng. Không gọi bước sau với dữ liệu hỏng.
- Ví dụ: trích số liệu đo từ một trang sổ tay → kiểm đơn vị và khoảng giá trị → viết tóm tắt.

### 3. Routing và chạy song song

- **Routing:** một lời gọi phân loại câu hỏi bằng structured outputs có `enum` (ví dụ `quy_trinh`, `so_lieu`, `khac`), code chọn hàm xử lý theo nhãn. Luôn có nhánh dự phòng cho nhãn lạ.
- **Chạy song song:** chia phần (mỗi trang sổ tay một lời gọi, rồi gộp) và bỏ phiếu (nhiều lời gọi cùng câu hỏi, lấy đa số).
- Giới hạn số lời gọi đồng thời. Bắt lỗi có kiểu ở từng nhánh, một nhánh lỗi không làm sập cả lần chạy.
- Nhắc lại module 01 mục 7: SDK đã tự thử lại 429 và 5xx. Đừng bọc thêm vòng retry trong mỗi nhánh.

### 4. Orchestrator-workers và evaluator-optimizer

- **Orchestrator-workers:** một lời gọi trả danh sách việc con (structured outputs, mảng có giới hạn độ dài); mỗi worker làm một việc; một lời gọi cuối tổng hợp. Khác chạy song song ở chỗ danh sách việc do Claude lập, không định sẵn.
- **Evaluator-optimizer:** một lượt viết, một lượt chấm theo tiêu chí rõ (structured outputs: `dat` và `nhan_xet`), lượt sau sửa theo nhận xét. Luôn có trần số vòng.
- Mỗi mẫu in tổng số lời gọi và chi phí, vì cả hai nhân số lời gọi rất nhanh (module 06).

### 5. Vòng lặp agent

- Bắt đầu từ vòng lặp của module 03 mục 3 và bài 3 module 03. Thêm:
  - **Điều kiện dừng:** `stop_reason == "end_turn"`; số lượt tối đa; trần chi phí kiểm **trước** mỗi lời gọi (trần output theo `max_tokens`, cách tính ở module 06 mục 3).
  - **Xử lý `stop_reason == "max_tokens"`** giữa vòng lặp: text có thể rỗng vì thinking dùng hết trần (module 07 mục 4).
  - **Lịch sử append-only:** gửi lại lượt assistant nguyên vẹn; không rút gọn kết quả tool cũ; không dựng lại `system` (module 07 mục 7).
  - **Nhắc giữa chừng bằng message `system`**, ví dụ "Còn một lượt, hãy kết luận". Không sửa tham số `system` (prefix check).
- Nhắc `between_tools` chỉ dùng được trên `claude-sonnet-5-5` (theo `config/models.yaml`). Script dùng model mặc định của repo.
- Ghi chú: agent chạy lâu làm context lớn dần. Các cơ chế quản lý context của API chỉ đưa vào nếu docs hiện tại có, kèm ngày kiểm (xem "Nguồn cần kiểm").

### 6. An toàn và quan sát

- **Duyệt tool có tác dụng phụ:** tool chỉ đọc chạy ngay; `ghi_nhat_ky` cần một hàm duyệt (trong script là callback, ở ứng dụng thật là người bấm). Bị từ chối thì trả `tool_result` có `is_error` và lý do, để Claude đổi hướng.
- **Danh sách tool cho phép** theo từng nhiệm vụ. Tên tool lạ trả `is_error` kèm danh sách tool hiện có (module 03 mục 6).
- **Nội dung tool không đáng tin:** một trang sổ tay mẫu chứa câu chỉ dẫn chèn vào. Code giữ nó trong `tool_result`, không chép lên `system` hay message `system` (module 07 mục 7).
- **Trace:** mỗi bước một dòng JSON (lượt, tool, input, `stop_reason`, token, chi phí). Ghi vào thư mục tạm, không commit.
- **Chi phí cả lần chạy** = tổng `estimate_cost_usd` của mọi lời gọi. Nhắc lại điều hàm này bỏ sót (cache, module 06 mục 5).

## Bài tập

```bash
CHAM=exercises uv run pytest modules/08-agents-workflows -q
```

| Bài | Nội dung | Test kiểm |
|---|---|---|
| `bai1_chuoi_co_cong.py` | Viết cổng kiểm và chuỗi hai bước | Cổng chặn dữ liệu sai; khi cổng trượt, bước sau không được gọi (đếm `calls` của mock) |
| `bai2_dinh_tuyen.py` | Router theo nhãn `enum`, có nhánh dự phòng | Mỗi nhãn tới đúng hàm; nhãn lạ vào nhánh dự phòng |
| `bai3_agent_an_toan.py` | Vòng lặp agent có trần lượt, trần chi phí, bước duyệt và trace | Dừng đúng ở trần lượt và trần chi phí; `ghi_nhat_ky` chưa duyệt trả `is_error`; giữ thinking nguyên vẹn (mock trả 400 nếu sai); trace đủ số bước |

Kèm `solutions/`, `tests/test_module08.py`, `quiz.md` (10 câu), `references.md` (link và ngày kiểm).

## Kế hoạch mock mode

Mọi script và test chạy với `CLAUDE_MOCK=1`, không gọi mạng, không cần key (CLAUDE.md, luật 1). CI tự chạy mọi `modules/*/python/*.py`, nên script mới của module 08 vào CI mà không cần sửa `ci.yml`.

### Mock đã làm được

- Block thinking, prefix check, 400 khi block thinking bị sửa hoặc bỏ trong vòng tool.
- Vòng tool: `tool_use` → `tool_result` → câu trả lời; `is_error`; `disable_parallel_tool_use`.
- Structured outputs: trả một giá trị hợp lệ tối thiểu theo schema (`schema_instance`).
- Lỗi giả lập (`MockAnthropic(errors=[429, 529])`), `redacted=True`, luật vị trí message `system`.
- `usage` có token thinking đổi theo effort; `estimate_cost_usd`; bộ đếm `calls`.
- `ClaudeVi(client=...)` nhận một mock tạo sẵn, nên script và test chọn được cấu hình mock.

### Mock còn thiếu, đề xuất bổ sung trong `claude_vi`

Mỗi mục là một thay đổi riêng, có test trong `tests/test_claude_vi.py`, làm trước khi viết script dùng nó.

**Trạng thái (2026-11-18):** mục 1–3 đã có trong `claude_vi` (issue #19). Mục 1 bật bằng `MockAnthropic(multi_step=True)`. Mục 2 chỉ áp cho structured outputs (`output_config.format`): mock bỏ dấu, chữ thường, coi `_` là khoảng trắng rồi dò nguyên từ; input của tool vẫn lấy phần tử đầu. Mục 3 là một khoá quanh mỗi lời gọi.

| # | Thiếu gì | Hệ quả nếu không sửa | Đề xuất |
|---|---|---|---|
| 1 | Mock gọi **mọi** tool ở lượt đầu, rồi trả lời ngay khi thấy `tool_result` | Vòng lặp agent luôn dừng sau một vòng tool; không minh hoạ được agent nhiều bước | Chế độ bật bằng tham số (tên chốt khi làm): mỗi lượt gọi **một** tool chưa có kết quả trong lịch sử, theo thứ tự trong `tools`; đủ kết quả thì trả lời. Hành vi suy ra từ request như phần còn lại của mock, không phải fixture viết tay. Mặc định giữ nguyên để test module 03 vẫn xanh |
| 2 | `schema_instance` luôn chọn phần tử đầu của `enum`; `boolean` là `false`, số là `0` | Router luôn đi nhánh đầu; evaluator không bao giờ "đạt" | Hoặc mock chọn giá trị `enum` có xuất hiện trong lượt user cuối (giống cách mock tìm `search_result`), hoặc chỉ dựng `Message` trong test. Bài 4 dùng chính hành vi "không bao giờ đạt" để minh hoạ trần số vòng |
| 3 | Mock không khoá khi nhiều luồng dùng chung (`calls`, bộ đếm id, bảng chữ ký thinking) | Bài chạy song song có thể ra kết quả không ổn định | Mỗi luồng một `ClaudeVi` (đơn giản nhất), hoặc thêm khoá trong mock. Trước khi dạy dùng chung một client thật giữa các luồng, kiểm docs SDK |
| 4 | Mock không điền token cache | Chi phí cả lần chạy bỏ qua cache | Không sửa trong module này. Ghi rõ giới hạn, như module 06 mục 5 |

### Test trong CI

- `modules/08-agents-workflows/tests/test_module08.py` chấm lời giải; `CHAM=exercises` chấm bài học viên.
- Test có thể dựng `Message` bằng tay (CONTRIBUTING.md cho phép trong test) để thử nhánh mà mock không tạo ra.
- Bốn lệnh trong CLAUDE.md phải xanh. Chạy thật chỉ qua `scripts/chay_that.py --dong-y` khi Nghiệp đồng ý.

## Model và chi phí

- Model mặc định là `default_model` trong `config/models.yaml` (hiện là `claude-haiku-5-5`). Script đọc model qua `Settings`, không viết model ID trong code.
- `between_tools` chỉ nhắc cho model có `between_tools_allowed: true` trong config. Không dùng `tool_choice` any/tool (CLAUDE.md, luật 4).
- Không thêm giá mới. Trần chi phí và tổng chi phí đọc `price_per_mtok` trong config.

## Nguồn cần kiểm khi viết

CLAUDE.md luật 6: kiểm từ nguồn hiện tại và ghi ngày kiểm trong `references.md`. Chưa mục nào dưới đây được kiểm cho module 08.

| Chủ đề | Nguồn | Dùng ở |
|---|---|---|
| Định nghĩa workflow và agent; các mẫu workflow | [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) | Bài 1–4 |
| Thiết kế tool cho agent | [Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) (đã dùng ở module 03) | Bài 5, 6 |
| Luật `tool_use`/`tool_result`, nội dung tool không đáng tin | [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) (đã dùng ở module 03) | Bài 5, 6 |
| Thinking trong vòng tool, prefix check, message `system` giữa hội thoại | Các trang docs trong `modules/07-thinking/references.md` | Bài 5 |
| Quản lý context cho agent chạy lâu | Docs platform.claude.com, tìm khi viết | Bài 5, chỉ đưa vào nếu docs hiện tại có |
| Thinking block gắn với lịch sử, ảnh hưởng vòng tool tự viết | [docs/kiem-chung-2026-10-21.md](kiem-chung-2026-10-21.md), điểm 2 | Bài 5 |

## Bẫy thường gặp (dự kiến)

- Dùng agent khi một workflow cố định là đủ.
- Vòng lặp không có trần lượt hoặc trần chi phí.
- Bỏ qua `stop_reason == "max_tokens"` giữa vòng lặp.
- Sửa tham số `system` mỗi lượt để nhắc "còn N lượt" → hỏng prefix. Dùng message `system`.
- Rút gọn kết quả tool cũ giữa chừng → hỏng prefix. Rút gọn trước khi gửi lần đầu.
- Bọc thêm retry quanh SDK trong mỗi nhánh song song.
- Tool có tác dụng phụ chạy không qua bước duyệt.
- Coi chữ trong kết quả tool là chỉ dẫn.
- Chỉ đo chi phí của lời gọi cuối.

## Điều gì đã thay đổi ở model 5.x (dự kiến)

Chỉ dùng những điều repo đã kiểm ở module 03 và 07.

| Trước đây | Bây giờ |
|---|---|
| Ép agent gọi tool bằng `tool_choice` any/tool | 400 trên hầu hết model 5.x; dùng `auto`, `strict: true` và chỉ dẫn trong prompt |
| Thinking giữa các lần gọi tool cần beta header | Adaptive thinking nghĩ xen giữa các lần gọi tool, không cần beta |
| Thinking của lượt cũ bị bỏ khỏi context | Được giữ lại và tính là input; agent dài tích luỹ thinking |
| Sửa `system` giữa chừng để đổi chỉ dẫn | Hỏng block thinking (prefix check); thêm message `system` |

## Câu hỏi cho Nghiệp

1. Mock nhiều bước (bảng mock, mục 1): bật bằng tham số mới của `MockAnthropic`, hay đổi hành vi mặc định?
2. Router và evaluator (mục 2): thêm luật chọn `enum` theo từ khoá trong mock, hay chỉ dựng `Message` trong test?
3. Tám script, mỗi script một ý, hay gộp còn 5–6 như các module trước?
4. Tên thư mục `modules/08-agents-workflows/` được chưa?
5. Module 08 có capstone riêng, hay để một capstone agent sau module 10?

## Sau khi duyệt

- Một issue code: bổ sung mock (mục 1–3) kèm test.
- Một issue nội dung: viết module 08 theo đề cương này.
- README: hàng 08 trong bảng lộ trình trỏ tới module khi có.
