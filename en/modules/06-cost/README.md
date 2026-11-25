# 06 · Cost

**Type:** Learn + Build · **Time:** about 2 hours · **Needs:** module 01 (section 5) and 07 (section 4) · **Cost:** $0 in mock mode; under $0.02 if you run it for real with `claude-haiku-5-5` (prices checked 2026-11-25 in [`config/models.yaml`](../../../config/models.yaml), see [references.md](references.md))

## Goals

After this module you can:

- Tell which numbers in `msg.usage` a call is billed on.
- Read prices from `config/models.yaml` instead of typing numbers into code.
- Work out the **cost cap** of a call **before** you send it, with the input counted by `count_tokens`.
- Turn on **prompt caching** in the right place, and price cache writes and cache reads correctly.
- Send work that is not urgent through the **Batch API** at half price, and match the results by `custom_id`.
- Know what **message threads** (beta) do for a request, and why they cannot replace the cache.

| Learn | Build |
|---|---|
| Read sections 1–9 and run the 5 scripts in `python/` | Do the 3 exercises in `exercises/`, graded by tests |

## Why learn this

The cost of a Claude app is not in one call. It is in that call times the number of users, the number of turns and the number of retries. A small number like $0.0005 becomes real money when you multiply it by millions.

You need two habits. Before a call: know the **most** this call can cost. After a call: know how much it **did** cost, and why. Then three tools to pay less for the same work: cache the part of the prompt that repeats, group work that is not urgent into a batch, and keep requests small when a conversation gets long.

## The minimum that runs

```bash
CLAUDE_MOCK=1 uv run python en/modules/06-cost/python/01_uoc_tinh_chi_phi.py
```

| Script | Main idea |
|---|---|
| [`01_uoc_tinh_chi_phi.py`](python/01_uoc_tinh_chi_phi.py) | Price table from the config, the output cap from `max_tokens`, splitting the cost from `usage` |
| [`02_prompt_caching.py`](python/02_prompt_caching.py) | Write the cache once, read it many times; a breakpoint in the wrong place; changing effort loses the cache; a prompt that is too short; break-even |
| [`03_dem_token.py`](python/03_dem_token.py) | `count_tokens` before the call, block requests over budget, compare the count with `usage` |
| [`04_batch.py`](python/04_batch.py) | Create a batch, wait for `ended`, match results by `custom_id`, compare the batch price with the normal price |
| [`05_message_threads.py`](python/05_message_threads.py) | Thread create/continue, resend the whole conversation on a 404, a thread with and without the cache |

The file names are Vietnamese: `uoc_tinh_chi_phi` = estimate the cost, `dem_token` = count tokens.

The scripts need no API key and make no network calls. The mock returns simulated `usage`: input tokens are counted by the rule **1 token ≈ 4 characters**, and thinking tokens change with `effort`. Those are mock numbers, not real ones. The **prices** are real prices, read from the config. The handbook used as a long prompt is [`data/so_tay_thiet_bi.md`](../../../modules/06-cost/data/so_tay_thiet_bi.md) ("equipment handbook"). It is fictional data, written in Vietnamese; the English scripts ask about it in English.

## 1. What you pay for

`msg.usage` has three main numbers (module 01, section 5):

- `input_tokens`: everything you send, including `system` and the whole conversation history (when you do not use prompt caching; with the cache, see section 5).
- `output_tokens`: everything Claude generates, **including thinking**, even when the thinking text is hidden.
- `output_tokens_details.thinking_tokens`: the thinking part inside `output_tokens`. Do not add it again.

The formula without the cache, with prices per million tokens (MTok):

```text
cost = input_tokens × input price / 1,000,000 + output_tokens × output price / 1,000,000
```

Two consequences:

- **In a long conversation, the input keeps growing.** Each turn resends the whole history, and on 5.x models the history also keeps the old thinking blocks (module 07, section 5).
- **Output usually costs more than input** for the same number of tokens. See the price table in section 2.

## 2. Prices per model: read them from the config

Prices live in one place only: `price_per_mtok` in [`config/models.yaml`](../../../config/models.yaml). The script reads it with `load_models()`:

```python
from claude_vi import load_models

gia = load_models()["models"][model]["price_per_mtok"]   # {"input": ..., "output": ...}  (gia = price)
```

Why not type the numbers into code: prices change over time and with new models. When they change, only the YAML changes; the scripts, the tests and `estimate_cost_usd` follow. If a model has no price in the config, `estimate_cost_usd` returns `nan`. It does not guess.

Part 1 of the script prints the price table of the `active` models in the config. A note from the config itself: the `price_per_mtok` of `claude-haiku-5-5` is the price for prompts up to 100,000 tokens; longer prompts cost more, and that price is under `long_context` (section 5).

## 3. Estimate before the call

`max_tokens` is a **hard** cap on all the output tokens of one call: thinking + text (module 07, section 4). So before you send, you already know:

```text
maximum output cost = max_tokens × output price / 1,000,000
```

That is the job of `tran_chi_phi_output(model, max_tokens)` in the script (`tran chi phi` = cost cap). With the repo's default `MAX_TOKENS=1024`, the table in part 1 of the script shows that this cap is very different from one model to another.

The input part is harder: you do not know the number of tokens before you send. There are two ways:

- **Measure once, reuse:** make an identical request (or run the mock with a fixture recorded from the real API), then read `input_tokens`.
- **Count tokens with the API:** `client.count_tokens(...)` (section 6).

An estimate before the call is for **blocking**, not for reporting. For example: refuse a job if the cost cap of the whole set of requests is over budget.

## 4. Read the cost after the call

`tach_chi_phi(msg)` in the script (`tach` = split) returns:

| Key | Meaning |
|---|---|
| `input` | `input_tokens × input price` |
| `output` | `output_tokens × output price` (thinking included) |
| `thinking` | the part of `output` that comes from thinking, only to look at, not added again |
| `tong` | (total) `input + output`; without the cache (and with a prompt under the `long_context` threshold) it equals `estimate_cost_usd(msg)` |
| `token_cache` | the number of cache write + cache read tokens; they have their own prices, split out in section 5 |

Part 3 of the script asks the same question with effort `low` and `high`. The input does not change; the output and the thinking part change with effort. To cut the cost over a whole set of requests, lower the effort. To be sure you never go over a limit, set `max_tokens` (module 07, section 4).

## 5. Prompt caching

**Prompt caching**: many requests start with the same long part (the tool list, the system prompt, a document). The API stores that first part. The next request reads the stored part instead of processing it again from scratch. You pay a little **more** on the write and much **less** on each read.

### Marking where to cache

Put `cache_control` on the **last block of the part that does not change**. That block and everything before it is the cached prefix:

```python
system = [
    {"type": "text", "text": "You are the lab's assistant."},
    {"type": "text", "text": SO_TAY, "cache_control": {"type": "ephemeral"}},   # breakpoint
]
client.create(system=system, messages=[{"role": "user", "content": question}])
```

- The prefix goes in the order **tools → system → messages**. Change one place, and the cache for that place and everything after it is lost.
- At most **4 breakpoints** per request. `claude_vi.rules` blocks more before sending.
- `ttl` (time to live): `"5m"` (the default) or `"1h"`. Each cache hit refreshes the cache at no extra cost. If you use both, the `1h` breakpoint must come before the `5m` breakpoint.
- A prompt shorter than the threshold is **not cached, and you get no error**. The threshold of the 5 active models is 512 tokens (`cache_min_tokens` in the config). Both cache fields in `usage` are then 0.
- **Automatic caching:** one `cache_control` field at the top level of the request. The API puts the breakpoint on the last cacheable block of `messages` (if the last block is not valid, it falls back to the nearest one) and moves it along as the conversation grows. It takes one of the 4 breakpoint slots. If the last block changes every time (the current time, a blank filled in later), put your own breakpoint at the end of the part that does not change instead of using automatic caching.

### Reading `usage` with the cache

```text
total input = cache_read_input_tokens + cache_creation_input_tokens + input_tokens
```

- `cache_creation_input_tokens`: tokens **written** to the cache in this request. `usage.cache_creation` splits them into `ephemeral_5m_input_tokens` and `ephemeral_1h_input_tokens`.
- `cache_read_input_tokens`: tokens **read** from the cache.
- `input_tokens`: only the part **after** the last breakpoint, at the normal input price.

`tach_input(msg)` in script 02 returns these four parts. Part 3 of the script shows call 1 writing, and calls 2 and 3 reading.

### Prices

Prices are in `cache_price_per_mtok` in the config, checked on the Pricing page on 2026-11-25:

| Token type | Compared with the input price |
|---|---|
| 5-minute cache write | 1.25x |
| 1-hour cache write | 2x |
| Cache read | 0.1x on Haiku 5.5 and older models; **0.05x** on Opus 5.5 and Sonnet 5.5; **0.025x** on Fable 5.2 and 5.1 |

The consequence, from the Pricing page: the 5-minute cache breaks even after **1 read**, the 1-hour cache after **2 reads**. Part 6 of script 02 works this out again for each model with the prices in the config. Exercise 1 makes you write it yourself.

`estimate_cost_usd(msg)` now counts 5-minute cache writes, 1-hour cache writes and cache reads. With Haiku 5.5, a prompt over 100,000 tokens (cache read and write tokens included) pays a higher price for **every** token type; the config keeps this price under `long_context`, and `estimate_cost_usd` uses it.

### What breaks the cache

- Editing a tool, the system prompt or an old message: lost from the edit onward.
- Changing the thinking settings: the messages part is always lost; on some models, tools and system too.
- Changing `effort`: **may** lose the messages part, and on some models tools and system too. Setting `effort` to exactly its default value does not lose it. Part 4 of script 02 shows this; the mock treats it as losing the whole prefix.
- Putting the breakpoint on a block that **changes every time** (the current time, the user's question): every call writes the whole prefix and never reads it. Part 2 of script 02 is an example.
- Not using it for longer than the TTL. There is no way to clear the cache by hand.
- Sending many requests in parallel at the very start: the cache is only usable after the first response starts, so the parallel requests all write. Wait for the first request to finish, then send the rest.

Adding instructions with a `system` message mid-conversation keeps the cache (module 07, section 7).

## 6. Count tokens before the call

`client.count_tokens(...)` calls `POST /v1/messages/count_tokens`. It takes almost the same parameters as `create` (`system`, `tools`, `messages`, `thinking`, images, PDFs) but **not** `max_tokens`. It returns a `MessageTokensCount` with one field, `input_tokens`.

```python
n = client.count_tokens(system=SO_TAY, messages=hoi).input_tokens          # hoi = the question
toi_da = (n * gia["input"] + max_tokens * gia["output"]) / 1_000_000        # toi_da = maximum
```

What to know (Token counting docs, checked 2026-11-25):

- **Free**, but it has its own requests-per-minute limit, separate from the Messages API limit.
- The count is an **estimate**. It can differ a little from the real `usage`. Tokens added by the system may be counted but are not billed.
- **No cache.** It accepts `cache_control`, but only `create` writes and reads the cache. The count is the total input, before taking out the part that will be read from the cache.
- The model's 400 rules still apply. For example: Opus 5.5, Sonnet 5.5 and Fable 5.2 refuse `tool_choice` any/tool even when counting tokens.
- Each model counts with its own tokenizer. From model 4.7 on, the same text gives about 30% more tokens than on older models (up to about 35% with Opus 5.5, depending on the content). Count again with the exact model you will use.
- Some inputs that `create` accepts make `count_tokens` return an error: server tools (except the advisor tool), the MCP connector, images/PDFs sent by `url` or `file` (Files API). Images and PDFs must be sent as base64.

Use `count_tokens` to **block**: part 2 of script 03 sends the request only when the cap is within budget. Exercise 2 makes you write that function.

## 7. Batch API: half price for work that is not urgent

**Message Batches API**: you send a set of requests, the API processes them asynchronously, and you get the results later. In return, every input and output token costs **50%** of the standard price (`batch_price_multiplier: 0.5` in the config).

```python
batch = client.batch_create([
    {"custom_id": "cau-000", "params": {"messages": [{"role": "user", "content": "..."}]}},
    ...
])
while client.batch_retrieve(batch.id).processing_status != "ended":
    time.sleep(30)
for r in client.batch_results(batch.id):
    if r.result.type == "succeeded":
        usd = estimate_cost_usd(r.result.message, batch=True)
```

The main rules (Batch processing docs, checked 2026-11-25):

| Item | Value |
|---|---|
| Size | at most 100,000 requests or 256 MB per batch |
| Time | most finish within 1 hour; after 24 hours, the requests still not done are `expired` |
| Results | a `.jsonl` file at `results_url`, kept for 29 days from when the batch was created |
| `custom_id` | 1–64 characters: letters, digits, `-`, `_`; unique within the batch |
| `processing_status` | `in_progress` → `ended` (or `canceling` → `ended` when canceled) |
| Result of each request | `succeeded` (billed), `errored`, `canceled`, `expired` (not billed) |

Three easy mistakes:

- **Results do not come back in the order you sent them.** Match them by `custom_id`. The mock reverses them on purpose so you can see it.
- **`params` are checked later.** A bad request only shows up as `errored` when the whole batch is done. `client.batch_create` checks the rules of each request **before** sending, so you do not wait hours to find out it was wrong.
- **Not allowed in a batch:** `stream: true`, fast mode (`speed`), `fallbacks`, `max_tokens: 0`, message threads.

Batch stacks with prompt caching: the two discounts multiply. But caching inside a batch is only "best-effort" (the docs give hit rates usually from 30% to 98%), because the requests run in parallel and in no fixed order. The docs advise using the 1-hour cache, sending one request first to write the cache, and only then sending the batch. The mock processes requests one by one, so it always hits; do not take the mock's number as what to expect.

## 8. Message threads (beta)

**Message threads** (launched in beta on 2026-11-02, header `anthropic-beta: message-threads-2026-08-12`): the API keeps the conversation on the server for a short time. The first turn is sent in full as usual, with `"thread": {"type": "create"}`. The next turns send only the **new message**, with `{"type": "continue", "previous_message_id": <id of the previous response>}`, and do not resend `system` and `tools`.

What it helps with: smaller requests, and a lower, steadier time to first token when the conversation is long, especially in an agent loop. **It does not make things cheaper.** The docs say: "Threads do not change pricing or rate limits." A thread **does not turn on the cache by itself**. To pay less, send the same top-level `cache_control` in **every** request of the thread. Each turn then reads the old part from the cache and writes the new turn. Parts 1 and 2 of script 05 compare the two ways.

The main rules (Message threads docs, checked 2026-11-25):

- The fixed fields must **stay the same** for the whole thread: `model`, `tool_choice`, `thinking`, `mcp_servers`, `context_management`, `output_config`, `skills` in `container`, the top-level `cache_control`, the set of beta headers (and whether `fallbacks` is present or not). If one differs, you get 400 `thread_fingerprint_mismatch`.
- `system` and `tools` are sent only in the create request. Sending them in a continue request, even with the value `null`, gives a 400.
- Each request with `thread` has at most 4 breakpoints. Breakpoints on the `system`/`tools` of the create request count again in every continue turn; the top-level `cache_control` counts as one. Too many gives 400 `thread_unsupported_request`.
- A thread is append-only. Each response `id` can be continued only **once** (the second time: 400 `thread_already_continued`).
- A thread is **best-effort**. It expires 5 minutes after the last request (each stored response resets the 5 minutes). A continue can also get a **404 `thread_not_found`** earlier for other reasons: the previous response is not finished or was not stored, a fallback model answered, or the request comes from another workspace or key. Your app must keep a copy of the whole conversation and resend it with a new create request. The class `HoiThoaiThread` in script 05 (`hoi thoai` = conversation) does this when the error code is `thread_not_found` (any other 404, for example a model that does not exist, is raised); part 3 simulates an expired thread.
- It cannot be used together with the Batch API or `count_tokens`. To count tokens, count the whole conversation.
- It is not eligible for ZDR (zero data retention).

Two limits of this repo:

- The installed `anthropic` SDK 1.17.0 has no `thread` parameter yet, so `claude_vi` sends it through `extra_body` together with the beta header. The docs describe an SDK helper `client.beta.messages.thread(...)`; the repo has not checked which SDK version has this helper.
- The docs do not say clearly how the old part of the conversation is billed on a continue. The mock assumes it is still billed as input, as when you resend it (because the docs say the price does not change). This is **the repo's own inference**; only numbers measured on a real run count.

## 9. Which tool to choose

| Situation | Tool |
|---|---|
| The same document or long system prompt for many questions | Prompt caching, breakpoint at the end of the part that does not change |
| A conversation with many turns | Automatic caching (top-level `cache_control`); add message threads if you need small requests |
| Hundreds of jobs that do not need an answer right away | Batch API, plus the 1-hour cache if they share a prefix |
| You must be sure you stay within budget | `count_tokens` + `max_tokens` to work out the cap before sending |
| You want each call to use less output | Lower `effort` (module 07) |

## Common traps

- **Adding `thinking_tokens` to `output_tokens`.** Thinking is already inside `output_tokens`; adding it again counts it twice.
- **Typing prices into code.** Prices change; read them from `config/models.yaml`.
- **Treating `estimate_cost_usd` as the bill.** It does not yet count the `inference_geo` multiplier (1.1x when you choose to run in the US), fast mode or server tools. See the real bill in the Console.
- **Pricing cache read tokens at the input price.** Cache reads have their own, much lower price; cache writes cost more than input.
- **A breakpoint on a part that changes every time.** You pay for cache writes forever and never read.
- **A prompt under the cache threshold.** No error, no cache; check `cache_creation_input_tokens` after the first call.
- **Changing effort between requests** that share a cache. Each change can force a new cache write.
- **Matching batch results by order.** Use `custom_id`.
- **Thinking message threads make things cheaper.** A thread makes the request smaller; the cache is what makes it cheaper.
- **Using an old model's token count for a new model.** The tokenizers differ; count again.
- **Looking at one call only.** Multiply by the number of turns, users and retries.
- **Setting `max_tokens` very tight to save money.** Thinking uses up the cap, the text is empty, and you still pay for the thinking (module 07, section 4).

## What changed with 5.x models

| Before | Now |
|---|---|
| Thinking off by default, costs nothing unless turned on | Adaptive thinking is on by default; thinking tokens count as output, even when the text is hidden |
| Thinking limited with `budget_tokens` | `budget_tokens` returns 400; cut the cost with `effort`, cap it with `max_tokens` |
| Thinking from old turns dropped from the context | Old thinking is kept and counts as input tokens in later turns |
| Cache reads at 0.1x the input price (still so on Haiku 5.5 and older models) | 0.05x on Opus 5.5 and Sonnet 5.5, 0.025x on Fable 5.1 and 5.2 |
| Cache threshold 1,024 to 4,096 tokens on 4.x models and Sonnet 5 | 512 tokens on all 5 active models |
| Token counts from old models | New tokenizer (from 4.7): about 30% more tokens for the same text |
| Each turn resends the whole conversation | Message threads (beta) added: send only the new message, same price |

## Exercises

| Exercise | Task | Graded on |
|---|---|---|
| [`bai1_chi_phi_cache.py`](exercises/bai1_chi_phi_cache.py) | Split the cost into input, 5-minute write, 1-hour write, cache read, output; the batch price; the number of reads to break even | matches `estimate_cost_usd`, break-even after 1 and 2 reads as in the docs |
| [`bai2_ngan_sach.py`](exercises/bai2_ngan_sach.py) | Count tokens, work out the cap, send only when within budget | over budget means no `create` call; count only once |
| [`bai3_batch.py`](exercises/bai3_batch.py) | Build requests with a valid `custom_id`, group the results by `custom_id` | any order; only `succeeded` is billed |

```bash
CHAM="$PWD/en/modules/06-cost/exercises" CLAUDE_MOCK=1 uv run pytest modules/06-cost -q   # grade your work
CLAUDE_MOCK=1 uv run pytest modules/06-cost -q                                          # grade the solutions
```

Review questions: [quiz.md](quiz.md).

## Next

Module 08 (agents and workflows) uses the habits from here: a cost cap for the whole agent loop, and reading `usage` on every turn. The sources of this module: [references.md](references.md).
