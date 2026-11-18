# 08 · Agents và workflows

**Loại:** Learn + Build · **Thời lượng:** khoảng 3 giờ · **Cần:** module 01–03 và 07; nên học 05 (structured outputs) và 06 (chi phí) · **Chi phí:** $0 ở mock mode; dưới $0,05 nếu chạy thật cả 8 script với `claude-haiku-5-5` và `MAX_TOKENS=1024` (ước tính từ giá trong [`config/models.yaml`](../../config/models.yaml), chưa đo; xem [references.md](references.md))

## Mục tiêu

Sau module này bạn:

- Phân biệt **workflow** (code định sẵn đường đi) với **agent** (Claude tự chọn bước tiếp theo), và chọn cách đơn giản nhất đủ dùng.
- Viết được các mẫu workflow: prompt chaining có cổng kiểm, routing, chạy song song, orchestrator-workers, evaluator-optimizer.
- Viết được một vòng lặp agent có đủ điều kiện dừng: `stop_reason`, số lượt tối đa, trần chi phí.
- Giữ lịch sử agent append-only và nhắc giữa chừng bằng message `system`, không làm hỏng block thinking.
- Chặn tool có tác dụng phụ bằng một bước duyệt, và coi kết quả tool là dữ liệu không đáng tin.
- Ghi trace từng bước và tính chi phí của cả lần chạy.

| Learn | Build |
|---|---|
| Đọc mục 1–6, chạy 8 script trong `python/` | Làm 3 bài trong `exercises/`, chấm bằng test |

## Vì sao học cái này

Module 03 đã có một vòng lặp tool. Module này biến nó thành thứ dùng được lâu: biết khi nào dừng, tốn bao nhiêu, và không làm điều nguy hiểm khi Claude hiểu sai.

Module 09 sẽ dùng Agent SDK, vốn che đi vòng lặp. Bạn cần thấy vòng lặp, điều kiện dừng và luật lịch sử trước khi giao chúng cho một thư viện.

## Tối thiểu chạy được

```bash
CLAUDE_MOCK=1 uv run python modules/08-agents-workflows/python/07_vong_lap_agent.py
```

Kịch bản xuyên suốt là một **trợ lý phòng thí nghiệm hư cấu**. Nó đọc sổ tay PTN của module 04 (`modules/04-rag/data/so_tay/`), dùng hai tool AQI và nhiệt độ của module 03 (`tools_mau.py`), và có thêm một tool có tác dụng phụ: `ghi_nhat_ky`. Mọi dữ liệu đều bịa.

| Script | Ý chính |
|---|---|
| [`01_mot_loi_goi.py`](python/01_mot_loi_goi.py) | Cùng một việc: một lời gọi so với workflow hai bước; số lời gọi, token, chi phí |
| [`02_chuoi_co_cong.py`](python/02_chuoi_co_cong.py) | Prompt chaining: cổng kiểm bằng code giữa hai bước, cổng trượt thì dừng |
| [`03_dinh_tuyen.py`](python/03_dinh_tuyen.py) | Routing: phân loại bằng `enum`, chọn hàm xử lý, nhánh dự phòng |
| [`04_song_song.py`](python/04_song_song.py) | Chạy song song: chia phần và bỏ phiếu; giới hạn đồng thời; một nhánh lỗi không làm sập lần chạy |
| [`05_dieu_phoi.py`](python/05_dieu_phoi.py) | Orchestrator-workers: Claude lập danh sách việc con, code chặn độ dài |
| [`06_danh_gia_sua.py`](python/06_danh_gia_sua.py) | Evaluator-optimizer: viết, chấm, sửa, có trần số vòng |
| [`07_vong_lap_agent.py`](python/07_vong_lap_agent.py) | Vòng lặp agent: ba điều kiện dừng, append-only, nhắc ở lượt cuối |
| [`08_duyet_va_trace.py`](python/08_duyet_va_trace.py) | Duyệt tool có tác dụng phụ, chỉ dẫn chèn vào trong tool, trace JSON, chi phí cả lần chạy |

[`phong_thi_nghiem.py`](python/phong_thi_nghiem.py) chứa phần dùng chung: client, tool, sổ chi phí.

Chạy cả 8: `for f in modules/08-agents-workflows/python/0*.py; do CLAUDE_MOCK=1 uv run python "$f"; done`

**Về mock của module này.** Các script dựng client bằng `tao_client()` trong `phong_thi_nghiem.py`. Ở mock mode hàm này dùng `MockAnthropic(multi_step=True)`: mỗi lượt mock gọi **một** tool chưa có kết quả, theo thứ tự trong `tools`, đủ kết quả thì trả lời. `ClaudeVi()` mặc định không bật chế độ này, nên agent sẽ dừng sau một vòng tool. Mock không hiểu câu hỏi: với structured outputs, `enum` được chọn theo từ khoá trong lượt user, số là `0`, chuỗi là `"[MOCK]"`, boolean là `false`. Các script dùng đúng những giới hạn này để minh hoạ cổng trượt và trần số vòng.

## 1. Workflow hay agent

Có ba nấc:

| Nấc | Ai quyết bước tiếp theo | Ví dụ |
|---|---|---|
| Một lời gọi | Không có bước tiếp theo | Hỏi đáp có tài liệu trong prompt (RAG, module 04) |
| Workflow | Code | Trích dữ kiện → kiểm → viết tóm tắt |
| Agent | Claude, trong một vòng lặp | Tự chọn đọc trang nào, tra số liệu nào, khi nào trả lời |

**Vì sao bắt đầu từ nấc thấp nhất:** mỗi nấc lên thêm đổi sự linh hoạt lấy độ trễ, chi phí và độ khó kiểm. Bài [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) khuyên tìm giải pháp đơn giản nhất có thể, và chỉ thêm độ phức tạp khi cần. Nhiều ứng dụng chỉ cần một lời gọi tốt kèm truy xuất và ví dụ.

[`01_mot_loi_goi.py`](python/01_mot_loi_goi.py) chạy cùng một việc theo hai cách. Cách hai bước tốn gấp đôi số lời gọi. Nó chỉ đáng khi bạn đo được là nó tốt hơn trên chính bài toán của mình.

## 2. Prompt chaining có cổng kiểm

Module 02 mục 7 đã giới thiệu chuỗi: mỗi bước một việc, đầu ra bước trước là đầu vào bước sau. Bài này thêm **cổng kiểm** (gate): code kiểm đầu ra của bước trước rồi mới gọi bước sau.

Cổng là **code**, không phải một lời gọi Claude nữa:

- đúng schema (structured outputs, module 05) — API lo phần này;
- đúng đơn vị, giá trị trong khoảng hợp lệ — code của bạn lo, vì structured outputs không nhận `minimum`/`maximum` (module 05);
- trích dẫn có thật (capstone c2 đối chiếu text từng trang).

Cổng trượt thì dừng chuỗi với lý do rõ ràng. Không gọi bước sau với dữ liệu hỏng: bước sau sẽ viết một tóm tắt trôi chảy về một con số sai.

Trong [`02_chuoi_co_cong.py`](python/02_chuoi_co_cong.py), mock trả `don_vi: "[MOCK]"`, nên cổng trượt và bước 2 không chạy. Phần cuối script đưa một kết quả hợp lệ qua cổng để thấy nhánh đi tiếp.

## 3. Routing và chạy song song

**Routing:** một lời gọi phân loại, code chọn hàm xử lý theo nhãn. Phân loại bằng structured outputs có `enum`, nên nhãn luôn nằm trong danh sách. Vẫn luôn có **nhánh dự phòng**, cho các trường hợp: `stop_reason` khác `end_turn` (ví dụ `refusal`), JSON hỏng, hay một nhãn mới thêm vào schema mà quên viết hàm.

Mỗi nhánh có thể rẻ hơn nhau rất nhiều. Trong [`03_dinh_tuyen.py`](python/03_dinh_tuyen.py), nhánh `khac` trả lời bằng một câu cố định, không tốn lời gọi nào. Nhánh `so_lieu` chạy một vòng tool.

**Chạy song song** có hai dạng:

- **Chia phần (sectioning):** mỗi phần một lời gọi chạy đồng thời, rồi code gộp. Ví dụ: tóm tắt từng trang sổ tay.
- **Bỏ phiếu (voting):** cùng một câu hỏi gọi nhiều lần, lấy đa số. Hợp với câu hỏi có/không mà sai một lần là đắt.

Ba điều luôn làm, xem [`04_song_song.py`](python/04_song_song.py):

1. Giới hạn số lời gọi đồng thời (`max_workers`). Không giới hạn thì tự gây 429.
2. Bắt lỗi **có kiểu** ở từng nhánh (`anthropic.APIError`, `OSError`). Một nhánh lỗi được báo lại, không làm sập cả lần chạy.
3. Không bọc thêm vòng retry trong mỗi nhánh. SDK đã tự thử lại 429 và 5xx (module 01 mục 7); thêm vòng nữa là nhân số lần thử.

Script dùng một `ClaudeVi` cho mỗi nhánh. Đây là cách đơn giản nhất. Repo chưa kiểm docs SDK về việc dùng chung một client thật giữa nhiều luồng, nên chưa dạy cách đó.

## 4. Orchestrator-workers và evaluator-optimizer

**Orchestrator-workers:** một lời gọi trả danh sách việc con, mỗi worker làm một việc, một lời gọi cuối tổng hợp. Khác chạy song song ở chỗ danh sách việc do Claude lập lúc chạy, không viết sẵn trong code. Vì vậy code phải:

- chặn độ dài danh sách (`TOI_DA_VIEC` trong [`05_dieu_phoi.py`](python/05_dieu_phoi.py)). Structured outputs bảo đảm đúng schema, không hứa độ dài mảng;
- chỉ cho chọn thứ có thật, bằng `enum` (tên trang sổ tay).

**Evaluator-optimizer:** một lượt viết, một lượt chấm theo tiêu chí rõ (structured outputs: `dat` và `nhan_xet`), lượt sau sửa theo nhận xét. **Luôn có trần số vòng.** Ở mock mode boolean luôn là `false`, nên [`06_danh_gia_sua.py`](python/06_danh_gia_sua.py) chạy tới trần: đó chính là điều xảy ra khi tiêu chí không bao giờ đạt được. Hết vòng thì dùng bản cuối và gắn cờ cần người xem.

Cả hai mẫu nhân số lời gọi rất nhanh. Mỗi script in tổng số lời gọi và chi phí của cả lần chạy (module 06).

## 5. Vòng lặp agent

Bắt đầu từ vòng lặp của module 03 mục 3. [`07_vong_lap_agent.py`](python/07_vong_lap_agent.py) thêm bốn thứ.

**Điều kiện dừng.** Kiểm theo thứ tự này mỗi lượt:

| Điều kiện | Kiểm khi nào | Vì sao |
|---|---|---|
| Trần chi phí | **Trước** mỗi lời gọi | Lời gọi sau có thể tốn tới `max_tokens × giá output` (module 06 mục 3). Kiểm sau thì đã muộn |
| `stop_reason != "tool_use"` | Sau mỗi lời gọi | `end_turn` là xong. `max_tokens`, `refusal`, `pause_turn` cần người gọi quyết |
| Số lượt tối đa | Cuối vòng `for` | Agent không bao giờ được lặp vô hạn |

Trần chi phí ở đây chỉ tính output. Input chưa biết trước, và lớn dần qua mỗi lượt vì lịch sử dài thêm. Muốn chặt hơn thì cộng một ước lượng input (đo từ lần chạy trước, module 06 mục 3).

**`stop_reason == "max_tokens"` giữa vòng lặp.** Thinking và text cùng tính vào `max_tokens`. Thinking có thể dùng hết trần, text rỗng (module 07 mục 4). Đừng dùng text đó như câu trả lời. Script dừng và báo rõ lý do.

**Lịch sử append-only.** Ba luật của module 07 mục 7, áp cho agent:

- gửi lại lượt assistant **nguyên vẹn**, kể cả block thinking;
- không rút gọn kết quả tool cũ giữa chừng; muốn gọn thì rút gọn **trước** khi gửi lần đầu;
- không dựng lại tham số `system` mỗi lượt.

Sai một trong ba thì prefix check làm block thinking hỏng: lỗi 400 trên tài khoản tạo từ 31/8/2026.

**Nhắc giữa chừng bằng message `system`.** Ở lượt cuối, script nối thêm `{"role": "system", "content": "Đây là lượt cuối được phép..."}` ngay sau lượt user chứa `tool_result`. Không sửa tham số `system`. Docs Mid-conversation system messages nói rõ: trong vòng lặp agent, đặt message `system` sau lượt `user` mang `tool_result`; với Sonnet 5.5 và Haiku 5.5, giữ lời nhắc của chương trình ở một message `system` riêng, không trộn với lời của người dùng. Mock không đọc lời nhắc, nên ở mock mode agent vẫn gọi tool ở lượt cuối.

`{"type": "between_tools"}` (ít thinking nhất) chỉ dùng được trên model có `between_tools_allowed: true` trong config, hiện là `claude-sonnet-5-5`. Script dùng model mặc định của repo nên không bật.

**Ghi chú: agent chạy lâu.** Context lớn dần qua mỗi lượt. Docs hiện có [context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing) (beta, header `context-management-2025-06-27`): API tự xoá kết quả tool cũ hoặc block thinking cũ ở phía server, còn lịch sử phía bạn giữ nguyên. Trang này coi server-side compaction là cách chính cho hội thoại dài. `claude_vi` và mock chưa hỗ trợ các tính năng này, nên module không có script cho chúng. Ngày kiểm ở [references.md](references.md).

## 6. An toàn và quan sát

**Duyệt tool có tác dụng phụ.** Tool chỉ đọc chạy ngay. `ghi_nhat_ky` ghi vào nhật ký và không xoá được, nên cần một hàm duyệt: trong script là callback, ở ứng dụng thật là người bấm nút. Bị từ chối thì trả `tool_result` có `is_error: true` và lý do, để Claude đổi hướng hoặc báo người dùng. Không im lặng bỏ qua `tool_use`: thiếu `tool_result` là lỗi 400.

**Danh sách tool cho phép theo nhiệm vụ.** Chỉ gửi những tool mà nhiệm vụ cần. Code vẫn kiểm lại tên trước khi chạy. Tên lạ trả `is_error` kèm danh sách tool hiện có (module 03 mục 6).

**Nội dung tool không đáng tin.** Kết quả tool thường mang nội dung bạn không kiểm soát: trang web, e-mail, file người dùng tải lên. Kẻ xấu có thể cài chỉ dẫn vào đó (indirect prompt injection). Trang mẫu [`data/99_ghi_chu_ca_dem.md`](data/99_ghi_chu_ca_dem.md) có một câu như vậy. Code giữ nó trong `tool_result`, không chép lên `system` hay message `system`: Claude coi message `system` là chỉ dẫn của nhà phát triển. Docs Handle tool calls khuyên đúng điều này.

**Trace.** Mỗi lời gọi một dòng JSON: lượt, `stop_reason`, tool đã gọi kèm input, token, chi phí. [`08_duyet_va_trace.py`](python/08_duyet_va_trace.py) ghi vào thư mục tạm của hệ điều hành, không vào repo. Trace là thứ bạn đọc đầu tiên khi agent làm điều lạ.

**Chi phí cả lần chạy** = tổng `estimate_cost_usd` của **mọi** lời gọi. Hàm này vẫn bỏ qua token cache và các loại giá đặc biệt (module 06 mục 5).

## Bẫy thường gặp

- **Dùng agent khi một workflow cố định là đủ.** Đắt hơn, chậm hơn, khó kiểm hơn.
- **Vòng lặp không có trần lượt hoặc trần chi phí.**
- **Kiểm trần chi phí sau khi gọi.** Lời gọi vượt trần đã xảy ra rồi.
- **Bỏ qua `stop_reason == "max_tokens"` giữa vòng lặp.** Text có thể rỗng.
- **Sửa tham số `system` mỗi lượt** để nhắc "còn N lượt" → hỏng prefix. Dùng message `system`.
- **Rút gọn kết quả tool cũ giữa chừng** → hỏng prefix. Rút gọn trước khi gửi lần đầu.
- **Bọc thêm retry quanh SDK** trong mỗi nhánh song song.
- **Chạy song song không giới hạn** → tự gây 429.
- **Tin độ dài danh sách việc con** mà orchestrator trả về.
- **Tool có tác dụng phụ chạy không qua bước duyệt.**
- **Coi chữ trong kết quả tool là chỉ dẫn**, hoặc chép nó lên `system`.
- **Chỉ đo chi phí của lời gọi cuối.**

## Điều gì đã thay đổi ở model 5.x

Chỉ những điều repo đã kiểm ở module 03, 07 và trong [references.md](references.md).

| Trước đây | Bây giờ |
|---|---|
| Ép agent gọi tool bằng `tool_choice` any/tool | 400 trên Opus 5.5, Sonnet 5.5, Fable 5.x; dùng `auto`, `strict: true` và chỉ dẫn trong prompt |
| Thinking giữa các lần gọi tool cần beta header | Adaptive thinking tự nghĩ xen giữa các lần gọi tool, không cần beta |
| Thinking của lượt cũ bị bỏ khỏi context | Được giữ lại và tính là input; agent dài tích luỹ thinking |
| Sửa `system` giữa chừng để đổi chỉ dẫn | Hỏng block thinking (prefix check); thêm message `system` sau lượt user |

## Bài tập

```bash
CHAM=exercises uv run pytest modules/08-agents-workflows -q
```

| Bài | Nội dung | Test kiểm |
|---|---|---|
| [`bai1_chuoi_co_cong.py`](exercises/bai1_chuoi_co_cong.py) | Cổng kiểm và chuỗi hai bước | Cổng chặn dữ liệu sai; cổng trượt thì bước 2 không được gọi (đếm lời gọi) |
| [`bai2_dinh_tuyen.py`](exercises/bai2_dinh_tuyen.py) | Router theo nhãn `enum`, có nhánh dự phòng | Mỗi nhãn tới đúng hàm; nhãn lạ, JSON hỏng, `refusal` vào nhánh dự phòng |
| [`bai3_agent_an_toan.py`](exercises/bai3_agent_an_toan.py) | Vòng lặp agent có trần lượt, trần chi phí, bước duyệt và trace | Dừng đúng ở từng trần; `ghi_nhat_ky` chưa duyệt trả `is_error` và không chạy; giữ thinking nguyên vẹn (mock trả 400 nếu sai); trace đủ số bước |

Test chạy ở mock mode, không cần key. Lời giải trong [`solutions/`](solutions/). Tự kiểm tra: [quiz.md](quiz.md). Nguồn và ngày kiểm: [references.md](references.md).

Module này chưa có capstone riêng. Một capstone agent sẽ đến sau module 10.

## Tiếp theo

Module 09 — Agent SDK: giao vòng lặp, điều kiện dừng và quản lý tool cho một thư viện, khi bạn đã biết chúng làm gì.
