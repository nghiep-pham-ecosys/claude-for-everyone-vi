# 03 · Tool use

**Type:** Learn + Build · **Time:** about 3 hours · **Cost:** $0 in mock mode; under $0.01 if you run it for real with `claude-haiku-5-5` (prices checked 2026-10-24, see [references.md](references.md))

## Goals

After this module you can:

- Define a tool with a good description and a strict schema.
- Write one tool use round by hand: `tool_use` → run the function → `tool_result`.
- Write a multi-turn loop that handles several tools called in parallel.
- Return a tool error to Claude with `is_error`.
- Explain why you must send the thinking blocks back unchanged in a tool loop.

| Learn | Build |
|---|---|
| Read sections 1–6 and run the 5 scripts in `python/` | Do the 3 exercises in `exercises/`, graded by tests |

## Why learn this

Claude only produces text. **Tool use** (also called function calling) lets Claude ask your code to do work for it: query a database, call an API, compute something. It is the foundation of every agent (modules 08–10).

The key point: **Claude does not run your code itself.** It returns a structured request. Your code decides whether to run it, then sends the result back.

## The minimum that runs

```bash
CLAUDE_MOCK=1 uv run python en/modules/03-tool-use/python/01_mot_tool.py
```

| Script | Main idea |
|---|---|
| [`tools_mau.py`](python/tools_mau.py) | Two sample tools (AQI, temperature) with made-up data, shared by the scripts |
| [`01_mot_tool.py`](python/01_mot_tool.py) | One tool use round, written by hand step by step |
| [`02_vong_lap.py`](python/02_vong_lap.py) | A multi-turn loop, several tools called in parallel |
| [`03_tool_choice.py`](python/03_tool_choice.py) | `auto`, `auto` + `disable_parallel_tool_use`, `none` |
| [`04_loi_tool.py`](python/04_loi_tool.py) | A tool error → `is_error` with a useful message |
| [`05_giu_thinking.py`](python/05_giu_thinking.py) | Drop the thinking block → 400; send it unchanged → it works |

In mock mode: when there are `tools`, on the first turn the mock calls **every** tool once (in parallel), with the first valid value from the schema as input (for example the first item of an `enum`). When it gets a `tool_result`, the mock answers by repeating the result.

## 1. One tool use round

```text
you  ── messages + tools ─────────────▶ Claude
you  ◀── stop_reason="tool_use", tool_use block {id, name, input}
you: run the function name(**input)
you  ── + assistant turn (msg.content unchanged)
        + user turn [tool_result {tool_use_id, content}] ──▶ Claude
you  ◀── stop_reason="end_turn", the answer
```

The three fields of a `tool_use` block: `id` (to match the result), `name`, and `input` (following `input_schema`). A `tool_result` block has `tool_use_id`, `content` (a string or a list of blocks), and `is_error` (optional).

## 2. Define a good tool

A tool has `name`, `description` and `input_schema`; optionally `strict` and `input_examples`.

- **`name`** must match `^[a-zA-Z0-9_-]{1,128}$`: no accented letters, no spaces. With several services, add a prefix (`env_get_aqi`, `github_list_prs`).
- **The `description` is the most important factor** for tool use quality, according to the docs. Write at least 3–4 sentences: what the tool does, when to use it (and when not to), what each parameter means, and what the tool does **not** return.
- **Merge related actions** into fewer tools (one tool with an `action` parameter instead of `create_x`, `update_x`, `delete_x`).
- **Return little, but useful**: only the fields Claude needs for the next step.

### Strict tool use

Add `"strict": true` and the API **guarantees** that `input` always matches the schema (right types, all required fields, and a valid `name`). A strict schema follows the same limits as structured outputs (module 02): `additionalProperties: false`, no `minimum`/`maxLength`... At most 20 strict tools in one request.

## 3. The tool loop

One question may need several rounds of tool calls. Loop until `stop_reason != "tool_use"`:

1. Send `messages` + `tools`.
2. `stop_reason == "tool_use"`: append the assistant turn (**`msg.content` unchanged**), run **every** `tool_use` block, and send **every** `tool_result` in **one** user turn.
3. Repeat. **Always set a limit on the number of turns**, so the agent cannot loop forever and burn money.

Format rules (break them and you get 400; `claude_vi` blocks them first):

- The `tool_result` must be in the user turn **right after** the assistant turn with the `tool_use`.
- Every `tool_use` must have a matching `tool_result`.
- In that user turn, the `tool_result` blocks must come **first**; any text goes after them.

The Python SDK has a **tool runner** that does this loop for you. The repo teaches the loop by hand first, so you understand what the tool runner hides.

## 4. Send thinking back unchanged

On 5.x models, an assistant turn with `tool_use` usually has a `thinking` block in front (often with an empty `thinking` field, because the text is hidden). When you send it back in the loop:

- **Send `msg.content` as it is.** Do not filter by type, do not reorder, do not rebuild the blocks.
- If you do filter blocks by type, keep both `thinking` and `redacted_thinking`.
- Editing a thinking block in the latest assistant turn → 400 *"thinking blocks ... cannot be modified"*.
- A thinking block is also tied to the conversation before it: change `system`, `tools` or an old turn and send it again, and you can get 400. Keep the history append-only.

[`05_giu_thinking.py`](python/05_giu_thinking.py) shows both cases. The repo's mock returns this exact 400 error, so exercise 3 goes red if you get it wrong.

## 5. `tool_choice`

| Value | Meaning | In this repo |
|---|---|---|
| `{"type": "auto"}` | Claude decides whether to call a tool (the default when there are `tools`) | ✅ |
| `{"type": "auto", "disable_parallel_tool_use": true}` | At most one tool per turn | ✅ |
| `{"type": "none"}` | No tool calls | ✅ |
| `any` / `tool` (force a tool call) | **400** on Opus 5.5, Sonnet 5.5, Fable 5.1. Haiku 5.5 accepts it, but then skips thinking | ❌ not used |

To make Claude use tools more, say it in the prompt: *"Use the tools to check before you answer."* To make the tool input always match the schema, use `strict: true`. To give the **answer** a fixed format, use structured outputs.

## 6. When a tool fails, and untrusted content

- The tool raises an exception → **do not** let the loop crash, and do not hide the error either. Send a `tool_result` with `"is_error": true` and a useful message: what happened and what to do next ("Rate limit, retry in 60 seconds"), not just "failed".
- Claude calls a tool name that does not exist → return `is_error` with the list of tools that do exist.
- **Tool results are untrusted data** (web pages, emails, files users upload): they can hold harmful instructions (indirect prompt injection). Keep that content **inside the `tool_result`**; do not copy it into `system` or into a user text block.

Cost: tool definitions, `tool_use` blocks and `tool_result` blocks all count as tokens. Also, when there are `tools`, the API adds a system prompt for tools: 286 tokens with `auto`/`none` on Haiku 5.5, Sonnet 5.5 and Opus 5.5.

## Common traps

- **Dropping the thinking block** when you send the assistant turn back → 400.
- **Sending each `tool_result` in its own user turn** when Claude calls several tools in parallel. Put them all in one turn.
- **Putting text before the `tool_result`** in the user turn.
- **Missing a `tool_use`** (running only the first tool).
- **A loop with no turn limit.**
- **A one-line tool description.** Claude picks the wrong tool or fills in the wrong parameters.
- **A tool name with accents or spaces.**
- **Using `tool_choice` any/tool** "to be safe" → 400 on most 5.x models.
- **Letting a tool exception crash the loop**, or returning `"failed"` with no reason.
- **Trusting the content of a tool result as instructions.**

## What changed with 5.x models

| Before | Now |
|---|---|
| `tool_choice={"type": "any"}` to force a tool call | 400 on Opus 5.5, Sonnet 5.5, Fable 5.1. Use `auto` + `strict: true` + an instruction in the prompt |
| Validate it yourself and retry when the tool input has the wrong type | `strict: true` guarantees the input matches the schema |
| The assistant turn had only text + tool_use | It usually has a `thinking` block in front; send it back unchanged |
| Edit the history freely between turns | A thinking block is tied to what came before it; keep the history append-only |
| The tool system prompt was about 500 tokens (Sonnet/Haiku 4.5) | 286 tokens on Haiku 5.5, Sonnet 5.5, Opus 5.5 |

## Exercises

```bash
CHAM="$PWD/en/modules/03-tool-use/exercises" uv run pytest modules/03-tool-use -q
```

| Exercise | Content |
|---|---|
| [`bai1_dinh_nghia_tool.py`](exercises/bai1_dinh_nghia_tool.py) | Build a strict tool; check the name, the description length, the required fields |
| [`bai2_chay_tool.py`](exercises/bai2_chay_tool.py) | `tool_use` → `tool_result`; an unknown tool and an exception → `is_error` |
| [`bai3_vong_lap.py`](exercises/bai3_vong_lap.py) | A full loop: parallel calls, keep thinking, a turn limit |

Solutions are in [`solutions/`](../../../modules/03-tool-use/solutions/). Check yourself: [quiz.md](quiz.md). Sources: [references.md](references.md).

## Next

Capstone c2, extracting lab data from a PDF: combine citations (module 05) and structured outputs (module 02) in a multi-step pipeline.
