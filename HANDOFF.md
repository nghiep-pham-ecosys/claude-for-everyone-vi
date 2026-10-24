# HANDOFF — việc cần làm (bàn giao 24/10/2026)

Khung repo đã dựng và đã chạy thử: 12 test xanh, 2 checker sạch, `hello.py` chạy ở mock mode. Làm lần lượt từng bước; xong mỗi bước thì đánh dấu ở đây và báo Nghiệp.

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

> 🟡 **Xong phần làm, chờ Nghiệp review** (24/10/2026, PR `feat/module-01`, xếp chồng trên PR Bước 1). 5 script `python/01_…05_`, 3 bài + lời giải + `tests/test_module01.py`, `quiz.md` 10 câu, `references.md` (kiểm 24/10). `claude_vi` có `ClaudeVi.stream()` (mock validate từng event bằng `RawMessageStreamEvent`) và `MockAnthropic(errors=[...])` giả lập 429/529/500/400. `hello.py` đổi tên thành `01_hello.py`; CI chạy mọi `modules/*/python/*.py`. Chưa chạy với API thật.

Nội dung tự viết, tiếng Việt, kiểm từ https://platform.claude.com/docs:
- `README.md`: mục tiêu, Learn/Build, thời lượng, chi phí ước tính; vì sao → tối thiểu chạy được → bẫy thường gặp → "Điều gì đã thay đổi ở model 5.x".
- Chủ đề: cấu trúc request (`model`, `max_tokens`, `system`, `messages`), hội thoại nhiều lượt, đọc `content` blocks (thinking/text), `stop_reason`, `usage` và chi phí, streaming, xử lý lỗi (400/429/529, retry).
- `python/`: 4–5 script nhỏ, mỗi script một ý. Streaming: thêm hàm stream vào `claude_vi` (mock trả event giả lập, validate bằng type SDK) kèm test.
- `exercises/` + `solutions/` (3 bài, có test chấm tự động ở mock mode), `quiz.md` (8–10 câu), `references.md` (link + ngày kiểm).

Xong khi: mọi script chạy với `CLAUDE_MOCK=1`, 4 lệnh trong CLAUDE.md xanh. **Dừng và gửi Nghiệp review** trước khi sang module 02 — module 01 là khuôn mẫu.

## Bước 3 — Module 02 Prompt engineering, Module 03 Tool use

Theo khuôn module 01. Module 03 lưu ý: `tool_choice` chỉ dùng `auto`; dạy strict tool use; thinking block phải gửi lại nguyên vẹn trong tool loop.

## Bước 4 — Capstone c2: trích xuất dữ liệu thí nghiệm từ PDF

Cần structured outputs + citations. Dùng PDF mẫu tự tạo hoặc giấy phép mở (ghi nguồn ở NOTICE.md). Đề bài: vật liệu/môi trường/đo lường — không hoá chất nguy hiểm.

## Còn treo (cần key thật — chờ Nghiệp quyết)

- Haiku 5.5: `forced_tool_choice_allowed` và `thinking_disabled_allowed` đang là giả định (`true`). Bước 1 trả lời được ý thứ hai qua Models API; ý thứ nhất cần một request thật.
  - Cập nhật 24/10: trang docs [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) ghi rõ Haiku 5.5 nhận `thinking: {"type": "disabled"}` ở effort `high` trở xuống, và trang [Errors](https://platform.claude.com/docs/en/api/errors) chỉ liệt kê Opus 5.5, Sonnet 5.5, Fable 5.1, Mythos 5.1 là cấm forced tool use. Hai giả định khớp docs; vẫn nên xác nhận bằng request thật.
- Ghi fixture thật bằng `CLAUDE_RECORD=1`.
