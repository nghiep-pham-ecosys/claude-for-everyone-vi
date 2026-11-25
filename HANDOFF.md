# HANDOFF — việc cần làm (bàn giao 24/10/2026)

Khung repo đã dựng và đã chạy thử: 12 test xanh, 2 checker sạch, `hello.py` chạy ở mock mode. Cập nhật 24/10/2026: Bước 0–4 xong và đã merge vào `main` (104 test xanh). Cập nhật 09/11/2026: Nghiệp duyệt thứ tự Bước 5–9 bên dưới; **vẫn chưa dùng API** — code phải sẵn sàng để cắm key là chạy (mục "Khi cắm key"). Làm lần lượt từng bước; xong mỗi bước thì đánh dấu ở đây và báo Nghiệp.

## Bước 0 — Tạo repo và push (làm đầu tiên)

> ✅ **Xong 24/10/2026.** Repo Private `pqnghiep1354/claude-for-everyone-vi`, `ci` xanh trên `main` (job `test`; `live-smoke` skipped; không có Environment).
> ⚠️ Secret scanning + push protection **chưa bật được**: API trả 422 "Secret scanning is not available for this repository" — repo private trên tài khoản cá nhân cần GitHub Secret Protection (trả phí). Thay thế miễn phí: bật *Push protection for yourself* ở github.com/settings/security_analysis (theo tài khoản, áp cho mọi repo bạn push). Nghiệp tự bật.

```bash
cd claude-for-everyone-vi
git init -b main
uv sync && uv run pytest -q          # phải xanh trước khi push
git add -A
git commit -m "chore: khung repo, wrapper claude_vi có mock mode, checker CI"
gh auth status                        # phải là tài khoản pqnghiep1354
gh repo create pqnghiep1354/claude-for-everyone-vi --private --source . --push \
  --description "Lộ trình học Claude không chính thức bằng tiếng Việt — từ API tới agent"
```

Sau đó:
- Bật **secret scanning + push protection** (Settings → Code security).
- Kiểm tra workflow `ci` chạy xanh trên GitHub Actions (job `test`). **Không** tạo Environment `live-api` và không thêm key.

Xong khi: repo Private tồn tại, `ci` xanh trên `main`.

## Bước 1 — `scripts/model_sync.py` (không cần key khi chạy test)

> ✅ **Xong 24/10/2026** (PR `feat/model-sync`). `tests/test_model_sync.py` chạy bằng fixture bịa 2 trang; job `model-sync` trong `ci.yml` để `if: false`. `--write` chỉ sửa model đã có (thinking_disabled_allowed, status, max_tokens, server_tools) — không tự thêm/xoá model vì luật 2. Chưa chạy với API thật.

Mục tiêu: bảng luật trong `config/models.yaml` tự đối chiếu với Models API thay vì sửa tay.

- Gọi `GET /v1/models` (phân trang). Với mỗi model đọc `id`, `capabilities.thinking.types.disabled.supported`, `capabilities.server_tools`, `max_tokens`.
- So với `config/models.yaml`: model mới chưa có, model biến mất, `thinking_disabled_allowed` lệch với `disabled.supported`.
- In báo cáo diff; cờ `--write` cập nhật YAML (giữ comment, ví dụ dùng `ruamel.yaml`); cờ `--issue` tạo issue qua `gh` (không chạy trong test).
- Test bằng response giả lập trong `tests/fixtures/models_list.json` — **không gọi mạng trong test**.
- Thêm job hằng tuần vào `ci.yml` nhưng để `if: false` cho tới khi có key.

Xong khi: test của `model_sync` xanh, README mục "Ba nguyên tắc" nhắc tới script này.

## Bước 2 — Module 01 Messages API hoàn chỉnh (khuôn mẫu cho mọi module)

> ✅ **Xong 24/10/2026**, Nghiệp duyệt và đã merge (PR #2). 5 script `python/01_…05_`, 3 bài + lời giải + `tests/test_module01.py`, `quiz.md` 10 câu, `references.md` (kiểm 24/10). `claude_vi` có `ClaudeVi.stream()` (mock validate từng event bằng `RawMessageStreamEvent`) và `MockAnthropic(errors=[...])` giả lập 429/529/500/400. `hello.py` đổi tên thành `01_hello.py`; CI chạy mọi `modules/*/python/*.py`. Chưa chạy với API thật.

Nội dung tự viết, tiếng Việt, kiểm từ https://platform.claude.com/docs:
- `README.md`: mục tiêu, Learn/Build, thời lượng, chi phí ước tính; vì sao → tối thiểu chạy được → bẫy thường gặp → "Điều gì đã thay đổi ở model 5.x".
- Chủ đề: cấu trúc request (`model`, `max_tokens`, `system`, `messages`), hội thoại nhiều lượt, đọc `content` blocks (thinking/text), `stop_reason`, `usage` và chi phí, streaming, xử lý lỗi (400/429/529, retry).
- `python/`: 4–5 script nhỏ, mỗi script một ý. Streaming: thêm hàm stream vào `claude_vi` (mock trả event giả lập, validate bằng type SDK) kèm test.
- `exercises/` + `solutions/` (3 bài, có test chấm tự động ở mock mode), `quiz.md` (8–10 câu), `references.md` (link + ngày kiểm).

Xong khi: mọi script chạy với `CLAUDE_MOCK=1`, 4 lệnh trong CLAUDE.md xanh. **Dừng và gửi Nghiệp review** trước khi sang module 02 — module 01 là khuôn mẫu.

## Bước 3 — Module 02 Prompt engineering, Module 03 Tool use

> ✅ **Xong 24/10/2026**, đã merge: module 02 (PR #3), module 03 (PR #4).
> `claude_vi` mô phỏng thêm: effort (token thinking), structured outputs (JSON đúng schema), tool use (gọi song song, `disable_parallel_tool_use`, `none`, forced bỏ thinking), và trả 400 khi block thinking trong vòng lặp tool bị sửa. `rules.py` chặn thêm: thinking `enabled`/`between_tools` sai model, effort lạ, schema strict/structured outputs không hợp lệ, tên tool sai, tool_result thiếu/sai chỗ.

Theo khuôn module 01. Module 03 lưu ý: `tool_choice` chỉ dùng `auto`; dạy strict tool use; thinking block phải gửi lại nguyên vẹn trong tool loop.

## Bước 4 — Capstone c2: trích xuất dữ liệu thí nghiệm từ PDF

> ✅ **Xong 24/10/2026**, đã merge (PR #5). Pipeline 3 bước vì citations + structured outputs không dùng chung được (docs Citations): lượt 1 citations lấy trích dẫn + trang, lượt 2 structured outputs với `enum` id nguồn, bước 3 code đối chiếu text từng trang (`pypdf`). PDF mẫu tự sinh (`data/tao_pdf_mau.py`, ghi ở NOTICE.md). Mock đọc PDF thật để trả `page_location`. Chưa chạy với API thật.

Cần structured outputs + citations. Dùng PDF mẫu tự tạo hoặc giấy phép mở (ghi nguồn ở NOTICE.md). Đề bài: vật liệu/môi trường/đo lường — không hoá chất nguy hiểm.

## Bước 5 — Sẵn sàng chạy API thật (không gọi API)

> ✅ **Xong 09/11/2026** (PR `chore/san-sang-api`).
> - `Settings.from_env()` nạp `.env` ở gốc repo trước khi đọc biến. Trước đây `.env` chỉ được nạp sau khi đã đọc `CLAUDE_MODEL`/`MAX_TOKENS`/`CLAUDE_RECORD`, nên các biến này trong `.env` bị bỏ qua. Shell vẫn được ưu tiên.
> - Thiếu key mà không mock: `MissingKeyError` tiếng Việt thay cho `TypeError` của SDK.
> - `scripts/chay_that.py`: liệt kê (mặc định) hoặc chạy thật (`--dong-y`) cùng tập script với job `test`; `--gia-dinh` kiểm 2 giả định Haiku 5.5; `--ghi` ghi fixture. Job `live-smoke` dùng script này.
> - `conftest.py` ở gốc: test luôn dùng thư mục fixture rỗng, nên fixture ghi thật không làm đổi kết quả test.
> - Release notes 24/10–05/11 không đổi model nào; giới hạn request 32 → 128 MB (module 01 đã sửa).

## Bước 6 — Module 05 Structured outputs, PDF, Citations

> ✅ **Xong 09/11/2026** (PR `feat/module-05`), chờ Nghiệp duyệt. 5 script, 3 bài + lời giải + 17 test, `quiz.md` 10 câu, `references.md` (kiểm 09/11). `claude_vi` thêm: citations custom content (`content_block_location`), `citations_delta` khi stream, luật bật citations tất cả-hoặc-không, giới hạn gộp 24 optional / 16 union, chặn regex không hỗ trợ trong `pattern`. Chưa chạy với API thật.

Đặt trước 04 vì mock đã có sẵn (citations, structured outputs, đọc PDF) và capstone c2 đang dùng kiến thức này mà chưa module nào dạy. Theo khuôn module 01.

## Bước 7 — Module 07 Thinking

> ✅ **Xong 09/11/2026** (PR `feat/module-07`, xếp chồng trên module 05), chờ Nghiệp duyệt. 5 script, 3 bài + lời giải + 27 test, quiz 10 câu, references (kiểm 09/11). Thêm `claude-fable-5-2` (ra mắt 09/11) vào `config/models.yaml`, cùng 2 cờ mới cho mọi model active: `prefix_check`, `mid_conversation_system_allowed`. `claude_vi`: mock trả tóm tắt khi `display: "summarized"`, chữ ký riêng từng block, `MockAnthropic(redacted=True)`, prefix check (hành xử như tài khoản tạo từ 31/8/2026); rules chặn `display` sai, `between_tools` kèm trường khác, beta (`display: "updates"`, `block_binding`, effort theo message), và sai vị trí message `system`. Chưa chạy với API thật.

Adaptive thinking, `display: "summarized"`, effort, `between_tools` (Sonnet 5.5), block thinking trong lịch sử. Phần lớn đã có trong `claude_vi`.

## Bước 8 — Module 06 Chi phí

> ✅ **Xong 17/11/2026**, đã merge (PR #16). Script `modules/06-cost/python/01_uoc_tinh_chi_phi.py`, **18 test** trong `tests/test_module06.py` (đếm bằng `CLAUDE_MOCK=1 uv run pytest -q modules/06-cost`, 18/11/2026), `references.md`. Chạy ở chế độ mock; chưa chạy với API thật.

Prompt caching (mock cần thêm `cache_creation_input_tokens`/`cache_read_input_tokens`, `estimate_cost_usd` tính giá cache), token counting, Batch API, message threads (beta 02/11/2026).

## Bước 9 — Module 04 RAG

> ✅ **Xong 09/11/2026** (PR `feat/module-04`), chờ Nghiệp duyệt. Nghiệp chọn hướng BM25/embedding local. Repo dùng **BM25 thuần Python** (không thêm dependency, CI không tải model), hybrid BM25 có dấu + không dấu ghép bằng RRF; embedding local chỉ mô tả ở mục 7 README, chưa cài và chưa chạy thử. Kho mẫu: 7 trang sổ tay PTN hư cấu (`data/so_tay/`, ghi ở NOTICE.md). 5 script (2 script đầu không gọi API), 3 bài + lời giải + 11 test, quiz 10 câu, references kiểm 09/11. `claude_vi`: mock trả `search_result_location` (top-level và trong `tool_result`), rules chặn `search_result` sai hình dạng/vị trí. Chưa chạy với API thật.

PR #7, #8, #9 đã merge vào `main` ngày 09/11/2026.

## Module 08 Agents và workflows

> ✅ **Xong 18/11/2026**, đã merge: mock mở rộng (PR #21), module (PR #22). Đề cương ở `docs/de-cuong-module-08.md`. 8 script trong `modules/08-agents-workflows/python/` (`01_mot_loi_goi` → `08_duyet_va_trace`) cùng `phong_thi_nghiem.py` (tool dùng chung, `tao_client()`), 3 bài + lời giải + **31 test** trong `tests/test_module08.py` (đếm bằng `CLAUDE_MOCK=1 uv run pytest -q modules/08-agents-workflows`, 18/11/2026), `quiz.md` 10 câu, `references.md` (kiểm 18/11), dữ liệu hư cấu `data/99_ghi_chu_ca_dem.md`. `claude_vi`: `MockAnthropic(multi_step=True)` gọi lần lượt từng tool chưa có kết quả. Chi phí ước tính khi chạy thật dưới $0,05 (khoảng $0,041). Chưa chạy với API thật.
>
> Còn lại: chưa kiểm docs SDK về dùng chung một client giữa nhiều luồng (script 04 dùng một client mỗi nhánh); context editing và server-side compaction chỉ giới thiệu, `claude_vi` chưa hỗ trợ; module 09 (Agent SDK) và capstone agent (sau module 10) chưa có.

## Trang GitHub Pages và video

> 🚧 **25/11/2026** (issue #5, nhánh `feat/5-pages-site`). `scripts/build_site.py` dựng trang mục lục và một trang cho mỗi module từ README (chỉ thư viện chuẩn + `pyyaml`); test ở `tests/test_build_site.py`. Video ghi ở `docs/pages/videos.yaml`: để trống thì trang báo "video đang được sản xuất", không có khung nhúng; chỉ nhận link YouTube. Workflow `.github/workflows/pages.yml` dựng và đăng khi `main` đổi.
>
> Còn lại: bật Pages (Settings → Pages → Source: GitHub Actions) trước lần merge đầu; mỗi video đăng xong thì điền link vào `videos.yaml`. Module mới phải thêm một mục vào `videos.yaml` (thiếu thì build báo lỗi).

## Việc có hạn

- **Sau 30/11/2026:** Sonnet 4.5 retire. Đổi `status: retired` cho model này trong `config/models.yaml`.

## Khi cắm key (làm theo thứ tự, chờ Nghiệp nói rõ — luật 1)

1. Đặt spend limit cho workspace học tập trên Console. `cp .env.example .env`, điền `ANTHROPIC_API_KEY`, để `CLAUDE_MOCK=0`.
2. `uv run python scripts/chay_that.py --dong-y --gia-dinh --chi 01-messages-api/python/01_hello` — một request, xác nhận key chạy.
3. `uv run python scripts/chay_that.py --dong-y --gia-dinh` — mọi script + 2 giả định Haiku 5.5. Script nào lỗi thì sửa (mock có thể lệch API thật).
4. `uv run python scripts/model_sync.py` — đối chiếu `config/models.yaml` với Models API; lệch thì `--write`.
5. (Tuỳ chọn) `--ghi` để ghi fixture thật, xem lại rồi commit.
6. GitHub: tạo Environment `live-api` có reviewer, thêm secret `ANTHROPIC_API_KEY`; trong `ci.yml` đổi `model-sync` từ `if: false` thành `github.event_name == 'schedule'`.

## Còn treo (cần key thật — chờ Nghiệp quyết)

- Haiku 5.5: `forced_tool_choice_allowed` và `thinking_disabled_allowed` đang là giả định (`true`). Bước 1 trả lời được ý thứ hai qua Models API; ý thứ nhất cần một request thật.
  - Cập nhật 24/10: docs đã trả lời cả hai ý. [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking): Haiku 5.5 nhận `thinking: {"type": "disabled"}` ở effort `high` trở xuống. [Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools): Haiku 5.5 nhận `tool_choice` any/tool (khi đó bỏ thinking). Comment trong `config/models.yaml` đã cập nhật; vẫn nên xác nhận bằng request thật khi có key.
  - Cập nhật 09/11: `scripts/chay_that.py --dong-y --gia-dinh` kiểm cả hai bằng request thật khi có key.
- Ghi fixture thật bằng `CLAUDE_RECORD=1` (hoặc `chay_that.py --ghi`).
