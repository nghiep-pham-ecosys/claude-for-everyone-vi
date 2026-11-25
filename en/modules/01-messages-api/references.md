# Sources · Module 01

Every fact about the API, prices and model behavior in this module was checked on **2026-10-24** against the sources below. The lesson is written in this repo's own words, not copied. The English text is a translation of the Vietnamese edition; the check dates did not change.

| Topic | Source | Used for |
|---|---|---|
| Requests, multi-turn conversations, prefill removed, `system` messages mid-conversation | [Using the Messages API](https://platform.claude.com/docs/en/build-with-claude/working-with-messages) | Sections 1, 2, "What changed" |
| Full parameter reference | [Messages API reference](https://platform.claude.com/docs/en/api/messages/create) | Section 1 |
| The values of `stop_reason`, `stop_details` | [Handling stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons) | Section 4, exercise 2 |
| Thinking on by default, `display` defaults to `"omitted"`, thinking counts as output tokens and toward `max_tokens`; turning thinking off per model | [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) | Sections 3, 5, "What changed" |
| Error codes, `request-id`, the SDK retries 2 times and honors `retry-after`, errors for edited thinking blocks / blocks tied to another conversation | [Claude API errors](https://platform.claude.com/docs/en/api/errors) | Section 7, exercise 3 |
| The Messages API request size limit went from 32 MB to 128 MB on the Claude API (checked 2026-11-09) | [Release notes 2026-10-28](https://platform.claude.com/docs/en/release-notes/overview), [Request size limits](https://platform.claude.com/docs/en/api/overview#request-size-limits) | Section 7 |
| SSE event order, cumulative `usage`, `thinking_delta` / `signature_delta`, `error` events mid-stream | [Streaming messages](https://platform.claude.com/docs/en/build-with-claude/streaming) | Section 6 |
| Prices per MTok; Haiku 5.5 costs more for prompts over 100,000 tokens | [Pricing](https://platform.claude.com/docs/en/about-claude/pricing) | Section 5, estimated cost |
| Rate limits, spend limits | [Rate limits](https://platform.claude.com/docs/en/api/rate-limits) | Section 7 |
| The types `Message`, `RawMessageStreamEvent`, `OutputTokensDetails.thinking_tokens`, the error classes | `anthropic` Python SDK 1.17.0 (read from the installed source) | Mock, tests |

## Prices checked (2026-10-24, USD per million tokens)

| Model | Input | Output |
|---|---|---|
| `claude-haiku-5-5` (prompt ≤ 100,000 tokens) | 0.10 | 0.50 |
| `claude-sonnet-5-5` | 2 | 10 |
| `claude-opus-5-5` | 4 | 20 |
| `claude-fable-5-1` | 10 | 50 |

These match `price_per_mtok` in [`config/models.yaml`](../../../config/models.yaml). Prices can change; check the Pricing page again before you quote them.

## Estimated cost

5 scripts, 7 calls to the default model when run for real (01: 1; 02: 2; 03: 2, one with `max_tokens` 10; 04: 1; 05: 1). The Opus 5.5 call in script 05 is stopped on your machine; the 529/429 errors in script 05 are only simulated in mock mode. Worst-case output with Haiku 5.5 and `MAX_TOKENS=1024`: 6 × 1,024 × $0.50/MTok ≈ $0.003; input is negligible. The whole module costs under $0.01. This is an estimate (added 2026-11-18 from the prices in the table above), not yet measured with the real API.

## Notes from the check

- The docs mention API version `2026-10-21` (from this version on, sending `temperature`/`top_p`/`top_k` with **any** value is an error). SDK 1.17.0 still sends the header `anthropic-version: 2023-06-01`; this module does not change the version.
- The Thinking page confirms that Haiku 5.5 accepts `thinking: {"type": "disabled"}` at effort `high` or lower. This matches the assumption `thinking_disabled_allowed: true` in `config/models.yaml`.
