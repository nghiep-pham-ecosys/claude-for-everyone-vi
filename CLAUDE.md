# CLAUDE.md — claude-for-everyone-vi

Lộ trình học **không chính thức**, tiếng Việt, về nền tảng Claude (API → agent). Code MIT, nội dung CC BY 4.0. Chủ dự án: Nghiệp (GitHub `pqnghiep1354`). Kế hoạch việc cần làm nằm ở [HANDOFF.md](HANDOFF.md).

Theo dõi tiến độ: issue và board của org trên GitHub.

## Lệnh

```bash
uv sync
uv run pytest -q                              # mock mode, không gọi mạng
uv run python scripts/check_models.py         # model ID phải nằm trong config/models.yaml
uv run python scripts/check_legacy_params.py  # chặn pattern đã hỏng trên model 5.x
CLAUDE_MOCK=1 uv run python modules/01-messages-api/python/01_hello.py
```

Cả 4 lệnh phải xanh trước mỗi commit.

## Luật cứng

1. **Không dùng API key thật** cho tới khi Nghiệp nói rõ. Mọi thứ chạy với `CLAUDE_MOCK=1`. Không chạy job `live-smoke`.
2. **Model ID chỉ khai báo ở `config/models.yaml`.** Model mới phải kèm link release note. Không đoán ID.
3. **Bài học gọi Claude qua `claude_vi.ClaudeVi`**, không tạo `Anthropic()` trực tiếp. Lấy text bằng `text_of(msg)`, không bao giờ dùng `msg.content[0].text` (trên model 5.x block đầu có thể là `thinking`).
4. **Không dùng** `temperature`/`top_p`/`top_k`, `budget_tokens`, prefill assistant, `tool_choice` any/tool. Muốn minh hoạ cách cũ thì đặt trong `legacy/`.
5. **Không sao chép** `anthropics/courses` (CC BY-NC 4.0, archived) hay `prompt-eng-interactive-tutorial` (không có giấy phép). Chỉ liên kết. Tự viết nội dung tiếng Việt. Xem `NOTICE.md`.
6. **Dữ kiện về sản phẩm/giá/model phải kiểm từ nguồn hiện tại** (platform.claude.com/docs, release notes) và ghi ngày kiểm trong `references.md` của module. Không viết con số chưa xác minh (ví dụ số khoá Academy).
7. **Capstone khoa học:** không đề bài về tổng hợp chất nguy hiểm, mầm bệnh, vũ khí.
8. Repo **Public** từ 25/11/2026 (Nghiệp duyệt). Không xoá lịch sử, không force-push `main` nếu chưa hỏi.
9. Chữ "Claude" trong tên repo: README phải luôn giữ dòng "không chính thức, không được Anthropic bảo trợ". Không dùng logo Claude/Anthropic.

## Kiến trúc

- `config/models.yaml` — allowlist + luật từng model (nguồn sự thật cho mock và checker).
- `shared/py/claude_vi/` — wrapper: `rules.py` chặn request sẽ lỗi 400; `mock.py` trả fixture đã validate bằng `anthropic.types.Message` (fixture sai shape thì test đỏ); `client.py` có `CLAUDE_RECORD=1` để ghi fixture từ API thật.
- `scripts/` — checker cho CI; `model_sync.py` đối chiếu YAML với Models API (test bằng `tests/fixtures/models_list.json`). `tests/` cố ý dùng model sai nên bị loại khỏi `check_models`; `shared/` cố ý nhắc pattern cũ nên bị loại khỏi `check_legacy_params`.
- `modules/NN-ten/` — mỗi module: `README.md`, `python/NN_y.py` (mỗi script một ý), `exercises/` + `solutions/`, `tests/test_moduleNN.py` (chấm lời giải; `CHAM=exercises` để chấm bài học viên), `quiz.md`, `references.md`. Khuôn mẫu: module 01.
- `capstones/cN-ten/` — `README.md` (đề bài, tiêu chí), `pipeline.py` (phần nối cho sẵn), `exercises/` + `solutions/`, `tests/`, `data/`.
- `docs/kiem-chung-2026-10-21.md` — bảng đối chiếu dữ kiện; đọc trước khi viết nội dung.

## Văn phong

Tiếng Việt, câu ngắn, giải thích "vì sao" trước "làm thế nào". Thuật ngữ: giữ tiếng Anh cho tên kỹ thuật (prompt caching, tool use, effort), lần đầu xuất hiện thì giải thích bằng tiếng Việt. Mỗi module có mục "Bẫy thường gặp" và "Điều gì đã thay đổi ở model 5.x".

## Commit

Conventional commits (`feat:`, `docs:`, `chore:`), mỗi commit một việc. Làm trên nhánh, mở PR vào `main`.
