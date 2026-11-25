## Tóm tắt

<!-- Đổi gì và vì sao, 1-3 câu ngắn. -->

Refs #<số issue>

## Đã kiểm thế nào

<!-- Lệnh đã chạy và kết quả. Cả 4 lệnh trong CONTRIBUTING.md phải xanh. -->

- [ ] `CLAUDE_MOCK=1 uv run pytest -q`
- [ ] `uv run python scripts/check_models.py`
- [ ] `uv run python scripts/check_legacy_params.py`
- [ ] `CLAUDE_MOCK=1 uv run python modules/01-messages-api/python/01_hello.py`

## Checklist

- [ ] Tên PR theo mẫu `<type>(<scope>): <mô tả>` (feat, fix, chore, refactor, docs, test, ci). Check `pr-title` kiểm điều này.
- [ ] Thân PR ghi `Refs #<số issue>`, không dùng `Fixes` hay `Closes`.
- [ ] Chỉ chạy ở mock mode. Không có API key, `.env`, token hay fixture ghi từ API thật.
- [ ] Gọi Claude qua `claude_vi.ClaudeVi`; model ID chỉ nằm trong `config/models.yaml`.
- [ ] Dữ kiện mới có link docs chính thức và ngày kiểm trong `references.md`.
- [ ] Nội dung tự viết. Tôi đồng ý cấp phép code theo MIT và nội dung theo CC BY 4.0.
