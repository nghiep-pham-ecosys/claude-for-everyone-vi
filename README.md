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

Ký hiệu: ✅ xong · 🚧 đang làm · 📋 đã lên kế hoạch · 🤝 mở cho cộng đồng đóng góp.

| Cấp | Module | Trạng thái |
|---|---|---|
| Cơ bản | [00 Cài đặt](modules/00-setup/README.md) | ✅ |
| Cơ bản | [01 Messages API](modules/01-messages-api/README.md) | ✅ |
| Cơ bản | [02 Prompt engineering](modules/02-prompt-engineering/README.md) | ✅ |
| Trung cấp | [03 Tool use](modules/03-tool-use/README.md) | ✅ |
| Trung cấp | [04 RAG](modules/04-rag/README.md) | ✅ |
| Trung cấp | [05 Structured outputs, PDF và Citations](modules/05-structured-pdf-citations/README.md) | ✅ |
| Trung cấp | [06 Chi phí](modules/06-cost/README.md) | ✅ |
| Trung cấp | [07 Thinking](modules/07-thinking/README.md) | ✅ |
| Nâng cao | [08 Agents & workflows](modules/08-agents-workflows/README.md) | ✅ |
| Nâng cao | [09 Agent SDK](modules/09-agent-sdk/README.md) | ✅ |
| Nâng cao | 10 MCP | 📋 |
| Mở cho cộng đồng | 11 Claude Code · 12 Agent Skills · 13 Evals · 14 Production · 15 Research | 🤝 |

Thứ tự học gợi ý: 00 → 01 → 02 → 03 → 05 → 07 → 04 → 06 → 08 → 09. Lý do: module 04 nên học sau 05, module 06 cần module 07, module 08 cần 03 và 07, module 09 cần 08 (mục "Cần" ở đầu README mỗi module).

Capstone đầu tiên: [**trích xuất dữ liệu thí nghiệm từ PDF ra JSON có schema, kèm trích dẫn trang gốc**](capstones/c2-trich-xuat-pdf) — citations + structured outputs + kiểm chứng bằng code.

## Ba nguyên tắc của repo

1. **Mọi model ID nằm trong [`config/models.yaml`](config/models.yaml).** CI chặn model lạ hoặc đã retired. Bảng luật trong file này được [`scripts/model_sync.py`](scripts/model_sync.py) đối chiếu với Models API (`GET /v1/models`): báo model mới, model biến mất, `thinking_disabled_allowed` lệch API; `--write` sửa YAML, `--issue` mở issue.
2. **Mọi lời gọi đi qua [`claude_vi`](shared/py/claude_vi).** Wrapper chặn trước các request sẽ lỗi 400 trên model 5.x (sampling params, `budget_tokens`, prefill, `tool_choice` ép buộc) và có mock mode để CI không tốn tiền.
3. **Không sao chép nội dung có giấy phép hạn chế.** Xem [NOTICE.md](NOTICE.md) và [docs/kiem-chung-2026-10-21.md](docs/kiem-chung-2026-10-21.md).

## Chi phí

Mặc định `claude-haiku-5-5`, `MAX_TOKENS=1024`. Mỗi README module ghi chi phí ước tính. Hàm `estimate_cost_usd(msg)` tính từ `usage` thật.

## Giấy phép

Code: [MIT](LICENSE). Nội dung bài giảng: [CC BY 4.0](LICENSE-CONTENT).
