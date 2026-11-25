"""Module 01: handling errors.

Two kinds of errors to tell apart:
- A request error (400): sending it again unchanged fails again. You must fix the request.
- A temporary error (429, 500, 529): waiting and retrying can succeed.

Run:  CLAUDE_MOCK=1 uv run python en/modules/01-messages-api/python/05_errors.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))

import anthropic  # noqa: E402

from claude_vi import ClaudeVi, ModelRuleError, Settings, text_of  # noqa: E402
from claude_vi.mock import MockAnthropic  # noqa: E402

settings = Settings.from_env()

# 1) A 400 error caught on your machine: claude_vi knows each model's rules, so no request is spent.
try:
    # Opus 5.5 always thinks: sending "disabled" makes the API return 400
    ClaudeVi(settings).ask("Hello", model="claude-opus-5-5", thinking={"type": "disabled"})
except ModelRuleError as e:
    print("Stopped before sending (the wrapper message is in Vietnamese):\n", e, "\n")

# 2) Temporary errors. The real SDK retries ON ITS OWN 2 times (max_retries) with backoff, and honors retry-after.
#    The mock does not retry, so we simulate 529 then 429 to see what the exceptions look like.
client = ClaudeVi(settings, client=MockAnthropic(errors=[529, 429])) if settings.mock else ClaudeVi(settings)
for attempt in range(1, 4):
    try:
        msg = client.ask("Hello")
    except anthropic.RateLimitError as e:  # 429: over the rate limit
        print(f"Attempt {attempt}: 429, retry-after={e.response.headers.get('retry-after')}s, request_id={e.request_id}")
    except anthropic.OverloadedError as e:  # 529: the API is overloaded overall, not your fault
        print(f"Attempt {attempt}: 529 overloaded, request_id={e.request_id}")
    except anthropic.BadRequestError as e:  # 400: fix the request, do NOT retry
        print("400:", e.message)
        break
    else:
        print(f"Attempt {attempt}: success -> {text_of(msg)}")
        break

print("\nIn real code: set the number of attempts with Anthropic(max_retries=...); do not wrap your own retry loop.")
