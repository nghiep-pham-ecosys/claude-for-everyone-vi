# 00 · Setup
**Type:** Learn · **Time:** 30 minutes · **Cost:** $0
1. Install [uv](https://docs.astral.sh/uv/) and Python 3.11 or newer.
2. `uv sync`
3. Try it without a key: `CLAUDE_MOCK=1 uv run python en/modules/01-messages-api/python/01_hello.py`
4. Create an account at the [Claude Console](https://platform.claude.com). **Create a separate workspace for learning and set a spend limit on it**, then create an API key.
5. `cp .env.example .env`, fill in the key, and run step 3 again without `CLAUDE_MOCK=1`. Every variable in `.env` (`CLAUDE_MODEL`, `MAX_TOKENS`, `CLAUDE_RECORD`) takes effect. A variable set in your shell wins over `.env`.
6. (Optional) Run every script in the repo once for real: `uv run python scripts/chay_that.py` lists them, and adding `--dong-y` ("I agree") calls the API.

If there is no key and mock mode is off, `claude_vi` raises `MissingKeyError` with the fix, and sends no request.

Max and Team plans include monthly API credits. See [API credits for subscribers](https://platform.claude.com/docs/en/about-claude/api-credits-for-subscribers).
