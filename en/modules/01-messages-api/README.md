# 01 · Messages API

**Type:** Learn + Build · **Time:** about 2 hours · **Cost:** $0 in mock mode; under $0.01 if you run it for real with `claude-haiku-5-5` (prices checked 2026-10-24, see [references.md](references.md))

## Goals

After this module you can:

- Write a correct request: `model`, `max_tokens`, `system`, `messages`.
- Keep a multi-turn conversation without breaking the thinking blocks.
- Read a response the right way: `content` blocks, `stop_reason`, `usage`.
- Estimate the cost from `usage`.
- Stream an answer, and know when to stream.
- Tell an error you must fix in the request (400) from an error you only need to retry (429, 529).

| Learn | Build |
|---|---|
| Read sections 1–7 below and run the 5 scripts in `python/` | Do the 3 exercises in `exercises/`, graded by tests |

## Why learn this first

Everything else (tool use, RAG, agents) is Messages API calls put together. Get one detail wrong here, for example reading the text with `content[0]`, and it breaks in every later module.

## The minimum that runs

```bash
CLAUDE_MOCK=1 uv run python en/modules/01-messages-api/python/01_hello.py
```

Mock mode makes no network call and needs no key. The fake response has the same shape as the real API, including the `thinking` block at the front.

| Script | Main idea |
|---|---|
| [`01_hello.py`](python/01_hello.py) | The first call: read the blocks, `stop_reason`, tokens, cost |
| [`02_multi_turn.py`](python/02_multi_turn.py) | A multi-turn conversation: send the history again |
| [`03_stop_reason_usage.py`](python/03_stop_reason_usage.py) | What happens when `max_tokens` is too small; thinking tokens |
| [`04_streaming.py`](python/04_streaming.py) | Stream the text piece by piece, then get the full Message |
| [`05_errors.py`](python/05_errors.py) | A 400 error stopped on your machine; 429/529 errors and retry |

Run all 5: `for f in en/modules/01-messages-api/python/*.py; do CLAUDE_MOCK=1 uv run python "$f"; done`

## 1. The shape of a request

A minimal request has three required fields:

| Field | Meaning | Note |
|---|---|---|
| `model` | Which model answers | In this repo, only from [`config/models.yaml`](../../../config/models.yaml) |
| `max_tokens` | The cap on **output** tokens | Thinking counts toward this cap too |
| `messages` | The list of `user` / `assistant` turns | Must end with a `user` turn on 5.x models |

The most common optional field is `system`: instructions for the whole conversation (role, tone, constraints). Put it in the separate `system` parameter, not in a message.

```python
client.create(
    system="You are a teaching assistant. Answer in English.",
    messages=[{"role": "user", "content": "What is prompt caching?"}],
)
```

`claude_vi` fills in `model` and `max_tokens` from `.env` if you do not pass them.

## 2. Multi-turn conversations

**Why:** the API is *stateless*. It keeps nothing between two calls. Claude "remembers" an earlier turn only because you send that turn again.

**How:** after each response, append `{"role": "assistant", "content": msg.content}` to the history, then append the next user turn. See [`02_multi_turn.py`](python/02_multi_turn.py).

Two things matter on 5.x models:

- Send `msg.content` back **unchanged**, including a `thinking` block whose `thinking` field is empty. Do not filter it down to the text.
- The history is **append-only**. A thinking block is tied to the part of the conversation before it. If you edit `system` or an old turn and then send that block again, you can get a 400 error.

The cost effect: each turn sends the whole history again, so `input_tokens` grows with the length of the conversation. Module 06 uses prompt caching to cut this cost.

## 3. Reading the response: content blocks

`msg.content` is a **list** of blocks, not a string. On 5.x models thinking is on by default (adaptive thinking), so a response usually looks like this:

```text
content = [ thinking(thinking="", signature="..."), text(text="The answer...") ]
```

The thinking text is hidden by default (`display: "omitted"`). The block is still there; only its `thinking` field is empty.

So **always** read the text with `text_of(msg)`. It joins every `text` block and skips the others. The `content[0]` code in old tutorials picks up the thinking block by mistake.

## 4. `stop_reason`

Read `stop_reason` **before** you trust the text.

| Value | Meaning | What to do |
|---|---|---|
| `end_turn` | The answer finished naturally | Use the result |
| `stop_sequence` | Hit a string from the `stop_sequences` you set | Use the result; see `msg.stop_sequence` |
| `max_tokens` | Hit the `max_tokens` cap: **cut off** | Raise `max_tokens` or ask for a shorter answer |
| `model_context_window_exceeded` | The context window is full | Treat it as cut off; shorten the history |
| `tool_use` | Claude wants to call a tool | Module 03 |
| `pause_turn` | A server tool loop hit its limit | Send the assistant content back unchanged to continue |
| `refusal` | Claude refused | Read `msg.stop_details`; try another model or rephrase |

[`03_stop_reason_usage.py`](python/03_stop_reason_usage.py) asks the same question with `max_tokens=1024` and with `max_tokens=10`, so you can see `end_turn` and `max_tokens`.

## 5. `usage` and cost

`msg.usage` tells you how many tokens you pay for:

- `input_tokens`: everything you send (system plus the whole history).
- `output_tokens`: everything Claude generates, **thinking included**, even when the thinking text is hidden.
- `output_tokens_details.thinking_tokens`: the thinking part of `output_tokens` (it can be `None`).

Cost = `input_tokens × input price + output_tokens × output price`, with prices per million tokens (MTok). `estimate_cost_usd(msg)` does this math with the prices in `config/models.yaml`.

An example with Haiku 5.5 ($0.10 / MTok in, $0.50 / MTok out): 200 tokens in and 1,000 tokens out cost 200 × 0.10/10⁶ + 1,000 × 0.50/10⁶ ≈ **$0.00052**.

`estimate_cost_usd` is a rough estimate. It does **not** include: cache prices (module 06), the higher Haiku 5.5 price for prompts over 100,000 tokens, the `inference_geo` multiplier, or batch prices. Check your real bill in the Console.

## 6. Streaming

**Why:**

- The user sees text right away instead of waiting for the whole answer.
- A long request (many minutes) is easily cut by the network when it stays silent too long. The SDK refuses a non-streaming request if it estimates the request will take over 10 minutes.

**How:** use `client.stream(...)` as a context manager, exactly like the real SDK:

```python
with client.stream(messages=[{"role": "user", "content": "..."}]) as s:
    for chunk in s.text_stream:
        print(chunk, end="", flush=True)
    msg = s.get_final_message()   # the full Message, with usage and stop_reason
```

Underneath is a series of server-sent events: `message_start` → for each block: `content_block_start`, many `content_block_delta`, `content_block_stop` → `message_delta` (with `stop_reason` and `usage`) → `message_stop`. The delta types are `text_delta`, `thinking_delta` and `signature_delta`. `text_stream` takes only `text_delta`.

Note: the `usage` in `message_delta` is a **running total**, not an increment.

## 7. Handling errors

| Code | Type | Retry? |
|---|---|---|
| 400 | `invalid_request_error`: a bad request (or you hit a spend limit you set yourself) | No. Fix the request |
| 401 / 403 | Wrong key / no permission | No |
| 404 | Wrong path or ID | No |
| 413 | Request too large (Messages API on the Claude API: 128 MB since 2026-10-28, 32 MB before) | No |
| 429 | `rate_limit_error`: over the rate limit | Yes, following `retry-after` |
| 429 | `rate_limit_error` with `error.details.error_code = "enforced_spend_limit_reached"`: you hit the spend cap of your tier | No: there is no `retry-after`, and a retry keeps failing until the start of next month |
| 500 | `api_error`: an internal error | Yes, with backoff |
| 504 | `timeout_error` | Use streaming for long requests |
| 529 | `overloaded_error`: the API is overloaded overall | Yes, with backoff |

Three things to remember:

1. **The SDK already retries** connection errors, 429 and 5xx: 2 times, with exponential backoff, and it honors the `retry-after` header. To change this, use `Anthropic(max_retries=...)`. Do not wrap your own retry loop around it; that multiplies the number of attempts.
2. Catch typed exceptions (`anthropic.RateLimitError`, `anthropic.OverloadedError`, `anthropic.BadRequestError`...). Do not compare message strings.
3. Log `e.request_id` (or `msg._request_id`). You need it when you contact support.

`claude_vi` also stops, on your machine, the requests that are sure to fail with a 400 error on 5.x models. It reports them as `ModelRuleError` (the message is in Vietnamese), so you do not spend a request.

While streaming, an error can arrive **after** you got HTTP 200, as an `error` event. The SDK turns it into an exception while you iterate over the stream.

## Common traps

- **Reading the text with `content[0]`.** The first block is often thinking. Use `text_of(msg)`.
- **Not reading `stop_reason`.** An answer cut off at `max_tokens` still looks like a normal answer.
- **`max_tokens` too small on a model with thinking.** Thinking uses up the cap, and the text left is very short or empty.
- **Sending back only the text of the assistant turn.** You lose the thinking block; with tool use (module 03) you get a 400 error.
- **Editing old history midway** (changing `system`, deleting turns). The thinking blocks may no longer be valid.
- **Putting system instructions in the first message** instead of the `system` parameter.
- **Writing your own retry loop on top of the SDK retry.**
- **Treating `estimate_cost_usd` as the bill.** It skips cache, long-prompt prices and batch prices.
- **Copying old tutorial code with `temperature`.** It returns 400 on 5.x models, and Python SDK 1.0 and later dropped this parameter. See [legacy/](../../../legacy/README.md).

## What changed with 5.x models

| Before | Now |
|---|---|
| A response had only `text` blocks | Thinking is on by default; a `thinking` block usually comes first, and its text is hidden by default |
| `temperature`, `top_p`, `top_k` for control | Return 400; dropped from Python SDK 1.0 and later. Control with the prompt and `output_config.effort` |
| Prefill: end `messages` with an assistant turn to force a format | Returns 400. Use structured outputs (module 05) |
| `thinking={"type": "enabled", "budget_tokens": N}` | Dropped; use adaptive thinking plus effort (module 07) |
| Turn thinking off with `{"type": "disabled"}` | Of the models this repo uses, only Haiku 5.5 still accepts it (at effort `high` or lower). Sonnet 5.5 uses `{"type": "between_tools"}`. Opus 5.5 and Fable 5.1 cannot turn it off |
| Thinking was not tied to the history | A thinking block is tied to the conversation before it; keep the history append-only |
| `system` only at the start | You can insert a `role: "system"` message mid-conversation (after a user turn). See references |

## Exercises

Three exercises in [`exercises/`](exercises/), with solutions in [`solutions/`](../../../modules/01-messages-api/solutions/). Each exercise is a file with `raise NotImplementedError`. Fill in the code, then grade it:

```bash
CHAM="$PWD/en/modules/01-messages-api/exercises" uv run pytest modules/01-messages-api -q
```

`CHAM` tells the tests which folder to grade. Give it the full path of the English exercises folder, as above. The Vietnamese command `CHAM=exercises` grades the Vietnamese files.

| Exercise | Content |
|---|---|
| [`bai1_hoi_thoai.py`](exercises/bai1_hoi_thoai.py) | A `HoiThoai` ("conversation") class that keeps an append-only history and keeps the thinking blocks unchanged |
| [`bai2_stop_reason.py`](exercises/bai2_stop_reason.py) | Choose an action from `stop_reason`; add up tokens and cost for a whole conversation |
| [`bai3_retry.py`](exercises/bai3_retry.py) | Exponential backoff with jitter and `retry-after`; never retry a 400 error |

The tests run in mock mode and need no key. The 429/529 errors are simulated with `MockAnthropic(errors=[529, 429])`.

Check your theory: [quiz.md](quiz.md). Sources and check dates: [references.md](references.md).

## Next

Module 02, Prompt engineering: write `system` and prompts that give steady answers without `temperature`.
