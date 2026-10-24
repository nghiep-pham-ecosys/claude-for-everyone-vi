# Claude for Everyone (vi)

> Lộ trình học **không chính thức**, bằng tiếng Việt, về nền tảng Claude của Anthropic — từ gọi API đầu tiên tới agent đa tác tử.
>
> Dự án cộng đồng, **không liên kết và không được Anthropic bảo trợ**. "Claude" và "Anthropic" là thương hiệu của Anthropic PBC.

## Bắt đầu trong 5 phút (không cần API key)

```bash
git clone <repo> && cd claude-for-everyone-vi
uv sync
CLAUDE_MOCK=1 uv run python modules/01-messages-api/python/01_hello.py
```

Có key rồi? Sao chép `.env.example` thành `.env`, điền `ANTHROPIC_API_KEY`, bỏ `CLAUDE_MOCK=1`.

## Lộ trình

| Cấp | Module | Trạng thái |
|---|---|---|
| Cơ bản | 00 Cài đặt · 01 Messages API · 02 Prompt engineering | 🚧 đang viết |
| Trung cấp | 03 Tool use · 04 RAG · 05 Structured/PDF/Citations · 06 Chi phí · 07 Thinking | 📋 |
| Nâng cao | 08 Agents & workflows · 09 Agent SDK · 10 MCP | 📋 |
| Mở cho cộng đồng | 11 Claude Code · 12 Agent Skills · 13 Evals · 14 Production · 15 Research | 🤝 |

Capstone đầu tiên: **trích xuất dữ liệu thí nghiệm từ PDF ra JSON có schema, kèm trích dẫn trang gốc.**

## Ba nguyên tắc của repo

1. **Mọi model ID nằm trong [`config/models.yaml`](config/models.yaml).** CI chặn model lạ hoặc đã retired. Bảng luật trong file này được [`scripts/model_sync.py`](scripts/model_sync.py) đối chiếu với Models API (`GET /v1/models`): báo model mới, model biến mất, `thinking_disabled_allowed` lệch API; `--write` sửa YAML, `--issue` mở issue.
2. **Mọi lời gọi đi qua [`claude_vi`](shared/py/claude_vi).** Wrapper chặn trước các request sẽ lỗi 400 trên model 5.x (sampling params, `budget_tokens`, prefill, `tool_choice` ép buộc) và có mock mode để CI không tốn tiền.
3. **Không sao chép nội dung có giấy phép hạn chế.** Xem [NOTICE.md](NOTICE.md) và [docs/kiem-chung-2026-10-21.md](docs/kiem-chung-2026-10-21.md).

## Chi phí

Mặc định `claude-haiku-5-5`, `MAX_TOKENS=1024`. Mỗi README module ghi chi phí ước tính. Hàm `estimate_cost_usd(msg)` tính từ `usage` thật.

## Giấy phép

Code: [MIT](LICENSE). Nội dung bài giảng: [CC BY 4.0](LICENSE-CONTENT).
