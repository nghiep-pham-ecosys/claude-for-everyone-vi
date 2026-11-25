# 07 · Thinking

**Type:** Learn + Build · **Time:** about 2 hours · **Needs:** modules 01–03 · **Cost:** $0 in mock mode; under $0.01 if you run it for real with `claude-haiku-5-5` (prices checked 2026-10-24, see [references.md](references.md))

## Goals

After this module you can:

- Explain what thinking is, how it is billed, and why the `thinking` block is often empty.
- Read a thinking summary with `display: "summarized"`, and know that it is **not** the original thinking.
- Reduce or turn off thinking by the rules of each model.
- Choose between `effort` and `max_tokens` when you want to control cost.
- Handle `redacted_thinking`, streamed thinking, and thinking in a tool loop.
- Keep the history append-only, so the prefix check does not reject your thinking blocks.

| Learn | Build |
|---|---|
| Read sections 1–7 and run the 5 scripts in `python/` | Do the 3 exercises in `exercises/`, graded by tests |

## Why learn this

A model that answers in one pass must get it right the first time: no draft, no check, no change of direction halfway. On a problem with many steps (a proof, a hard bug, a long-running agent), the first approach is often not good enough. Thinking gives Claude room for a draft: read the question again, try an approach, check the intermediate results, drop the wrong approach, and only then answer.

On 5.x models thinking is **on by default**. You do not choose whether to use it; you choose how much, and you must write code that does not break it. The three earlier modules touched on thinking (`text_of`, keeping blocks in the tool loop). This module puts it all together into full rules.

## The minimum that runs

```bash
CLAUDE_MOCK=1 uv run python en/modules/07-thinking/python/01_doc_thinking.py
```

| Script | Main idea |
|---|---|
| [`01_doc_thinking.py`](python/01_doc_thinking.py) | `display` "omitted" and "summarized"; the billed tokens do not change |
| [`02_tat_thinking.py`](python/02_tat_thinking.py) | The table of rules to turn off or reduce thinking on each model (checked locally) |
| [`03_max_tokens.py`](python/03_max_tokens.py) | Thinking eats into `max_tokens`; the text is cut off or empty |
| [`04_stream_thinking.py`](python/04_stream_thinking.py) | `thinking_delta`, `signature_delta`, put together with `get_final_message()` |
| [`05_append_only.py`](python/05_append_only.py) | Changing `system` midway → 400; add an instruction with a `system` message |

The mock simulates: thinking tokens by effort, summary text with `summarized`, a separate signature for each block, `redacted_thinking` (turn it on with `MockAnthropic(redacted=True)`), the 400 error when you edit a thinking block in a tool loop, and the prefix check.

## 1. How thinking works

When thinking is on, the response has one or more `thinking` blocks **before** the `text` blocks:

```text
content = [ thinking(thinking="", signature="EqQB..."), text(text="The answer...") ]
```

- **`signature`**: an encrypted copy of the whole thinking. You cannot read it; you only send it back unchanged. The API decrypts it so Claude can go on from where it was thinking.
- **`thinking`**: the visible text. On 5.x models it is empty by default.
- **Cost**: thinking tokens count as **output tokens**, even when you see no text at all, and they count toward `max_tokens` together with the text.

The mode on 5.x models is **adaptive thinking**: Claude decides on its own whether to think and how deeply, based on how hard the task is and on `effort`. An easy question may have no thinking block at all. Do not write code that assumes the first block is always thinking; that is why you use `text_of(msg)` and filter blocks by `type`.

## 2. Reading thinking: `display`

| `display` | What the `thinking` block holds | Default on |
|---|---|---|
| `"omitted"` | The `thinking` field is empty; only the `signature` is there | Every 5.x model in this repo |
| `"summarized"` | A summary that is easy to read | Opus 4.6, Sonnet 4.6 and older |
| `"updates"` (beta) | Only the progress notes with text between tool calls | Needs a beta header; `claude_vi` does not support it |

```python
client.create(messages=[...], thinking={"type": "adaptive", "display": "summarized"})
```

Three things to know about `"summarized"`:

1. **It is a summary, not the original thinking.** Another model writes the summary. No setting returns the original chain of thought.
2. **The price does not change.** You pay for all of the original thinking tokens, not for the tokens of the summary. The token count you see does not match `output_tokens`.
3. **To see the reasoning, read the thinking block.** Do not ask for "explain your thinking step by step" in the answer. On Fable 5.x, Opus 5.5 and Sonnet 5.5, a request like that may be refused with `stop_details.category: "reasoning_extraction"`.

`"omitted"` is not cheaper. Its benefit is speed: when you stream, the server skips the thinking text, so the text of the answer arrives sooner.

### `redacted_thinking`

Sometimes part of the thinking is hidden for safety reasons. The API returns a `redacted_thinking` block with an encrypted `data` field and no text. Send it back unchanged, like a thinking block. A common trap: code that filters on `b.type == "thinking"` when it sends blocks back drops this block, and the tool loop fails with 400.

## 3. Reducing or turning off thinking

There is no common switch to turn it off. Each model has its own rules (Thinking docs, checked 2026-11-09):

| Model | `"disabled"` | `"between_tools"` | How to reduce thinking |
|---|---|---|---|
| Haiku 5.5 | Allowed, at effort `high` or lower | 400 | `disabled`, or a low effort |
| Sonnet 5.5 | 400 | Allowed, at effort `high` or lower | `between_tools` turns off the thinking at the start of the turn |
| Opus 5.5 | 400 | 400 | Only effort |
| Fable 5.1, Fable 5.2 | 400 | 400 | Only effort |

On every 5.x model, `thinking: {"type": "enabled", "budget_tokens": N}` (the old extended thinking) returns 400.

Details that are easy to get wrong:

- `disabled` or `between_tools` together with effort `xhigh`/`max` → 400. If you want less thinking, lower the effort first.
- `display` does not go with `disabled`. `between_tools` takes no other field.
- `between_tools` on Sonnet 5.5 still returns progress notes (with text) between tool calls.
- Haiku 5.5 with thinking off and a request for JSON: the model may skip a tool call it needed.

Do not copy these rules into your code. Read them from `config/models.yaml` (exercise 1), or from the Models API (`capabilities.thinking.types.disabled.supported`, `scripts/model_sync.py`). When a new model comes out, only the YAML changes.

[`02_tat_thinking.py`](python/02_tat_thinking.py) prints the table above by letting `claude_vi` check each combination on your machine. It sends no request.

## 4. Effort, `max_tokens` and cost

Two knobs, two different jobs:

| | `output_config.effort` | `max_tokens` |
|---|---|---|
| Kind | A behavior signal, **soft** | A **hard** cap |
| Effect | Every output token: thinking, length of the text, number of tool calls | Total thinking + text of this turn |
| When to use it | You want a whole set of requests to be cheaper or faster | You want to be sure you do not go over a spending level |

Defaults: `medium` on Haiku 5.5 and Opus 5.5; `high` on Sonnet 5.5, Fable 5.1 and Fable 5.2. Setting effort to the default gives exactly the same result as not setting it.

The order to debug high cost or a cut-off answer:

1. `stop_reason == "max_tokens"` and the text is empty → thinking used up the whole cap. **Raise `max_tokens`.** You paid for that thinking and got no answer.
2. High cost across a whole set of requests → **lower the effort**. It makes the whole response smaller, and thinking goes down with it.
3. Claude thinks too little on a hard task → raise the effort.
4. You need thinking fully off → `disabled` or `between_tools`, only on the models that allow it.

The docs advise: set effort explicitly, measure on your own task before you change the level, and when you use `high` or above, give `max_tokens` plenty of room. With `max_tokens` above 21,333, the Python SDK makes you use streaming (a client-side check to avoid HTTP timeouts).

In a conversation that uses prompt caching, changing effort or the thinking settings between requests breaks the cache (module 06). Effort per message (which keeps the cache) is in beta; `claude_vi` does not support it yet.

## 5. Thinking in a tool loop

Module 03 taught you: send the thinking blocks back **unchanged**, together with `tool_use`. The reason: for Claude, the whole tool loop is **one assistant turn**. When it gets the `tool_result`, Claude goes on with the same unfinished answer, so it needs the thinking from before.

Rules from the docs:

- **Required:** within a turn with tools, send back every `thinking` and `redacted_thinking` block, in the same order, unchanged, with none left out.
- **Recommended:** between turns, send all of them back. The API filters them itself and only bills the blocks it really puts into the context.
- **Allowed:** outside tool use, drop the thinking of older turns.
- **Do not change the thinking settings within a turn** (between `tool_use` and `tool_result`). The API does not return an error; it quietly turns off thinking for that request. Changing them between turns is fine.

With adaptive thinking (every 5.x model in this repo), Claude can think **between** tool calls (interleaved thinking) with no beta header, so thinking blocks can show up in many places in one turn. Fable 5.x, Opus 5.5 and Sonnet 5.5 can also write a short progress note before each tool call, as a separate thinking block.

On Haiku 5.5, Sonnet 5.5, Opus 5.5 and Fable 5.x, the thinking blocks of earlier turns are **kept** in the context. They count as input tokens, like the rest of the history. A long conversation builds up thinking; count tokens (module 06) to get it right.

## 6. Streaming thinking

A thinking block streams as `thinking_delta` events, then exactly one `signature_delta` right before `content_block_stop`. Only then does the text come. With `"omitted"`, each thinking block has just one empty `thinking_delta`, then the signature.

Do not join the deltas yourself to rebuild the block. Use `s.get_final_message()`: it puts the thinking and the signature together the right way, and you can send the result back right away. See [`04_stream_thinking.py`](python/04_stream_thinking.py).

## 7. Append-only history and the prefix check

This is the change most likely to break old code.

On Haiku 5.5, Sonnet 5.5, Opus 5.5, Fable 5.1 and Fable 5.2, a thinking block is valid only when **everything sent before it stays the same** in later requests. The API calls this the *prefix check*. Three things are checked:

- the `system` parameter;
- the `tools` list;
- every message before that block.

`effort`, `max_tokens`, `output_config` and `tool_choice` are not part of what is checked. Older thinking blocks are not either: dropping the oldest blocks (from the start of the history) is allowed, but dropping a block in the middle breaks the blocks after it.

When the check fails: accounts created on or after 2026-08-31 get a 400 error (`Invalid signature in thinking block. The block is bound to a different conversation...`) on every model listed above. Older accounts get a 400 only on Fable 5.2 (and Mythos 5.1/5.2); on the other models the mismatched block still reaches the model with no error. So **code that runs without errors on your key does not prove the code is right**: people who use your code with a new account will get a 400. This repo's mock always behaves like a new account.

What breaks the prefix, and what to do instead:

| Your code... | Do this instead |
|---|---|
| Rebuilds `system` every turn (adds the date and time, a mode flag) | Keep `system` fixed; add a new `{"role": "system", ...}` message |
| Rebuilds the context in the first user turn | Build it once and send it back exactly as it was; put what changes in the newest turn |
| Shortens old tool results | Shorten them **before** you send them the first time |
| Adds or removes tools midway | Mid-conversation tool changes (beta, not in `claude_vi` yet) |
| Rebuilds a saved session from a template | Save exactly what you sent and received, then replay it |
| Filters out some thinking blocks in the middle | Send the assistant turn back exactly as you received it |

### A `system` message mid-conversation

Instead of changing the `system` parameter, append a message with `role: "system"` at the point where the instruction starts to apply. The prefix stays the same, and so does the prompt cache. No beta header is needed on the 5.x models in this repo.

```python
messages = [u1, a1, u2, {"role": "system", "content": "From now on, answer in Vietnamese."}]
```

Position rules (break them and you get a 400; `claude_vi` stops it first):

- It must not be the first message. For an instruction from the start, use the `system` parameter.
- It must come **right after a user turn** (even a turn with only `tool_result`), and **before an assistant turn** or at the end of the list.
- It must not sit between a `tool_use` and its `tool_result`.

Do not put outside data (tool results, documents, web content) in a `system` message: Claude treats it as an instruction from the developer and follows it. Outside data still goes in a `tool_result`.

## Common traps

- **Getting the text with `content[0]`.** The first block is often thinking, or there is no thinking at all. Use `text_of(msg)`.
- **Thinking `"omitted"` is cheaper.** It is only faster; the price is the same.
- **Treating the thinking summary as the original thinking**, or counting its tokens to estimate cost.
- **Asking for "explain your thinking step by step" in the answer** → it may be refused with `reasoning_extraction`. Read the thinking block.
- **Sending `"disabled"` to Opus/Sonnet/Fable**, or `disabled` + effort `xhigh`.
- **Passing `"adaptive"` as the effort value.** `adaptive` is a thinking mode.
- **`max_tokens` too tight** → `stop_reason: "max_tokens"`, empty text, and you still pay for the thinking.
- **Filtering on `type == "thinking"` when you send blocks back** → `redacted_thinking` gets dropped, and the tool loop fails with 400.
- **Editing the text of a summarized thinking block** before you send it back → 400.
- **Changing the thinking settings between `tool_use` and `tool_result`** → thinking is quietly turned off.
- **Adding the date and time to `system` every turn** → prefix check 400 on new accounts.
- **Believing the code is right because your key gives no error.** Older accounts get looser rules.

## What changed with 5.x models

| Before | Now |
|---|---|
| Thinking off by default, turned on with `{"type": "enabled", "budget_tokens": N}` | Adaptive thinking on by default; `budget_tokens` returns 400; you control it with `effort` |
| Thinking came back as a summary (`display` defaulted to `"summarized"`) | Default `"omitted"`: the block is there, but the `thinking` field is empty |
| Turned off with `{"type": "disabled"}` on every model | Only Haiku 5.5 (effort ≤ `high`); Sonnet 5.5 uses `between_tools`; Opus 5.5 and Fable 5.x cannot turn it off |
| Interleaved thinking needed a beta header | Automatic with adaptive thinking |
| Thinking from old turns was dropped from the context | Haiku/Sonnet/Opus 5.5 and Fable 5.x keep it, and it counts as input tokens |
| Changing `system` mid-conversation was normal | It breaks thinking blocks (prefix check); use a `system` message mid-conversation |
| Thinking worked in any account | Blocks from Sonnet 5.5, Haiku 5.5 and Fable 5.2 only work in the account that created them |

## Exercises

```bash
CHAM="$PWD/en/modules/07-thinking/exercises" uv run pytest modules/07-thinking -q
```

| Exercise | Content |
|---|---|
| [`bai1_cau_hinh.py`](exercises/bai1_cau_hinh.py) | Choose the setup with the least thinking / to see the summary, reading the rules from `config/models.yaml` |
| [`bai2_bao_cao.py`](exercises/bai2_bao_cao.py) | Count blocks, the summary, the share of thinking tokens; diagnose `stop_reason` |
| [`bai3_append_only.py`](exercises/bai3_append_only.py) | An append-only conversation: new instructions as a `system` message, save and replay a session |

Solutions are in [`solutions/`](../../../modules/07-thinking/solutions/). Check yourself: [quiz.md](quiz.md). Sources: [references.md](references.md).

## Next

Module 06, Cost: prompt caching, counting tokens, the Batch API, message threads.
