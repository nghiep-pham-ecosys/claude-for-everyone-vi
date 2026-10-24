# Đóng góp

## Trước khi mở PR

```bash
uv run pytest                          # wrapper + luật model, mock mode
uv run python scripts/check_models.py  # model ID hợp lệ
uv run python scripts/check_legacy_params.py
```

## Quy tắc

- **Gọi Claude qua `claude_vi.ClaudeVi`**, không tạo `Anthropic()` trực tiếp trong bài học.
- **Không viết `msg.content[0].text`.** Dùng `text_of(msg)` — trên model 5.x block đầu có thể là `thinking`.
- **Không dùng** `temperature`, `top_p`, `top_k`, `budget_tokens`, prefill assistant, `tool_choice` any/tool. Muốn minh hoạ cách cũ → đặt trong `legacy/` và ghi rõ "chỉ để đọc".
- **Model mới:** thêm vào `config/models.yaml` kèm link release note. Không viết model ID ở nơi khác.
- **Notebook:** xoá output trước khi commit (`nbstripout`).
- **Fixture mock:** ghi bằng `CLAUDE_RECORD=1` từ API thật, không tự viết tay trừ trong test.
- **Mỗi module có `references.md`** ghi link chính thức và ngày kiểm tra.
- **Không chép** nội dung CC BY-NC hoặc không có giấy phép (xem NOTICE.md).
- **Capstone khoa học:** không đề bài liên quan tổng hợp chất nguy hiểm, mầm bệnh, vũ khí.
