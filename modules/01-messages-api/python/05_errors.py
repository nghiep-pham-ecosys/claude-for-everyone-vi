"""Module 01 — xử lý lỗi.

Hai loại lỗi cần phân biệt:
- Lỗi do request (400): gửi lại y nguyên vẫn lỗi. Phải sửa request.
- Lỗi tạm thời (429, 500, 529): đợi rồi thử lại có thể thành công.

Chạy:  CLAUDE_MOCK=1 uv run python modules/01-messages-api/python/05_errors.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

import anthropic  # noqa: E402

from claude_vi import ClaudeVi, ModelRuleError, Settings, text_of  # noqa: E402
from claude_vi.mock import MockAnthropic  # noqa: E402

settings = Settings.from_env()

# 1) Lỗi 400 bắt ngay tại máy: claude_vi biết luật từng model nên không tốn một request.
try:
    # Opus 5.5 luôn bật thinking: gửi "disabled" thì API trả 400
    ClaudeVi(settings).ask("Xin chào", model="claude-opus-5-5", thinking={"type": "disabled"})
except ModelRuleError as e:
    print("Chặn trước khi gửi:\n", e, "\n")

# 2) Lỗi tạm thời. SDK thật TỰ thử lại 2 lần (max_retries) với backoff, có tôn trọng retry-after.
#    Mock không tự retry, nên ta giả lập 529 rồi 429 để xem exception trông thế nào.
client = ClaudeVi(settings, client=MockAnthropic(errors=[529, 429])) if settings.mock else ClaudeVi(settings)
for attempt in range(1, 4):
    try:
        msg = client.ask("Xin chào")
    except anthropic.RateLimitError as e:  # 429: vượt rate limit
        print(f"Lần {attempt}: 429, retry-after={e.response.headers.get('retry-after')}s, request_id={e.request_id}")
    except anthropic.OverloadedError as e:  # 529: API quá tải chung, không phải lỗi của bạn
        print(f"Lần {attempt}: 529 overloaded, request_id={e.request_id}")
    except anthropic.BadRequestError as e:  # 400: sửa request, KHÔNG thử lại
        print("400:", e.message)
        break
    else:
        print(f"Lần {attempt}: thành công -> {text_of(msg)}")
        break

print("\nTrong code thật: chỉnh số lần thử bằng Anthropic(max_retries=...), đừng tự bọc thêm vòng retry.")
