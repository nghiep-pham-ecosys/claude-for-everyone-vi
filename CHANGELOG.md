# Nhật ký thay đổi

Mọi thay đổi đáng kể của repo ghi ở đây. Định dạng theo [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), số phiên bản theo [Semantic Versioning](https://semver.org/lang/vi/). Phiên bản trùng với `version` trong `pyproject.toml`.

## [Chưa phát hành]

_(chưa có)_

## [0.1.0] - 2026-11-25

Bản đầu tiên công khai. Mọi script, bài tập và test chạy ở **mock mode** (`CLAUDE_MOCK=1`). Chưa có gì được chạy với API thật.

### Nội dung khoá học

- 11 module, từ cơ bản tới nâng cao: 00 Cài đặt, 01 Messages API, 02 Prompt engineering, 03 Tool use, 04 RAG, 05 Structured outputs, PDF và Citations, 06 Chi phí, 07 Thinking, 08 Agents và workflows, 09 Agent SDK, 10 MCP.
- Mỗi module có bài đọc, script chạy được ở mock mode, bài tập kèm lời giải và test chấm tự động, quiz, và `references.md` ghi link docs chính thức cùng ngày kiểm.
- Capstone c2: trích xuất dữ liệu thí nghiệm từ PDF ra JSON có schema, kèm trích dẫn trang gốc. PDF mẫu do repo tự sinh, số liệu bịa.
- Trang khoá học trên GitHub Pages, mỗi module một trang, dựng từ README của module. Video của từng module đang được sản xuất.

### Công cụ

- Wrapper `claude_vi`: chặn trước các request sẽ lỗi 400 trên model 5.x; mock mode trả response đã validate bằng kiểu dữ liệu của SDK `anthropic`, có streaming, giả lập lỗi 429/529/500/400, tool use, thinking, citations, structured outputs và Agent SDK.
- `config/models.yaml` là nơi duy nhất khai báo model ID và luật từng model.
- Checker cho CI: `check_models.py` (model ID hợp lệ) và `check_legacy_params.py` (chặn pattern đã hỏng trên model 5.x).
- `model_sync.py` đối chiếu `config/models.yaml` với Models API; `chay_that.py` chạy các script với API thật khi có key. Cả hai chưa chạy thật.
- 441 test xanh ở mock mode (`CLAUDE_MOCK=1 uv run pytest -q`, 25/11/2026).

### Cộng đồng và CI

- Repo công khai từ 25/11/2026.
- `CONTRIBUTING.md` có quy trình review: fork hoặc nhánh, tên PR, 4 lệnh chạy trên máy, chỉ mock mode, ai review và merge, giấy phép của phần đóng góp.
- Form issue (báo lỗi, đề xuất nội dung, việc) và template PR bằng tiếng Việt. Hỏi đáp ở Discussions.
- Module 11-15 (Claude Code, Agent Skills, Evals, Production, Research) mở cho cộng đồng; mỗi module có một issue `good first issue` cho bước đề cương.
- CI: job `test` (mock mode, mọi script bài học, capstone), `gitleaks` quét toàn bộ lịch sử, `ci-result` và `pr-title` là hai check bắt buộc trước khi merge. Action được ghim theo commit SHA. Hook pre-push chạy gitleaks.

### Giới hạn đã biết

- Mock có thể lệch API thật. Hai giả định về Haiku 5.5 (`forced_tool_choice_allowed`, `thinking_disabled_allowed`) chờ một request thật để xác nhận.
- Sonnet 4.5 retire sau 30/11/2026; `config/models.yaml` sẽ đổi trạng thái của model này ở bản sau.

[Chưa phát hành]: https://github.com/nghiep-pham-ecosys/claude-for-everyone-vi/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/nghiep-pham-ecosys/claude-for-everyone-vi/releases/tag/v0.1.0
