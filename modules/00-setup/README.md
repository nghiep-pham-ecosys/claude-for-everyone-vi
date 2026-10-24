# 00 · Cài đặt

**Loại:** Learn · **Thời lượng:** 30 phút · **Chi phí:** $0

1. Cài [uv](https://docs.astral.sh/uv/) và Python ≥3.11.
2. `uv sync`
3. Chạy thử không cần key: `CLAUDE_MOCK=1 uv run python modules/01-messages-api/python/hello.py`
4. Tạo tài khoản tại [Claude Console](https://platform.claude.com), **tạo workspace riêng cho việc học và đặt spend limit**, rồi tạo API key.
5. `cp .env.example .env`, điền key, chạy lại bước 3 không có `CLAUDE_MOCK=1`.

Gói Max và Team có tín dụng API hằng tháng — xem [API credits for subscribers](https://platform.claude.com/docs/en/about-claude/api-credits-for-subscribers).
