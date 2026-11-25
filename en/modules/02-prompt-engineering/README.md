# 02 · Prompt engineering

**Type:** Learn + Build · **Time:** about 2.5 hours · **Cost:** $0 in mock mode; under $0.01 if you run it for real with `claude-haiku-5-5` (prices checked 2026-10-24, see [references.md](references.md))

## Goals

After this module you can:

- Write a prompt that is clear, gives reasons, and asks for a specific output format.
- Put a long document in the right place in the prompt, with its parts split by XML tags.
- Teach Claude with 3–5 examples (few-shot).
- Force a format with structured outputs instead of prefill.
- Choose an effort level instead of `temperature`.

| Learn | Build |
|---|---|
| Read sections 1–6 and run the 5 scripts in `python/` | Do the 3 exercises in `exercises/`, graded by tests |

## Why learn this

With the same model, a vague prompt gives a vague answer. Prompt engineering is the cheapest way to raise quality: no new model, no new infrastructure.

But before you change a prompt, you need to know what "better" means. The docs advise having three things ready: **clear success criteria**, **a way to measure** against them, and **a first draft of the prompt**. If you cannot measure, you cannot tell whether the new prompt is better (module 13 covers evals).

## The minimum that runs

```bash
CLAUDE_MOCK=1 uv run python en/modules/02-prompt-engineering/python/01_ro_rang.py
```

| Script | Main idea |
|---|---|
| [`01_ro_rang.py`](python/01_ro_rang.py) | A vague prompt and a clear prompt; say "why" in `system` |
| [`02_xml_tai_lieu.py`](python/02_xml_tai_lieu.py) | Several documents: XML, documents on top, the question at the end |
| [`03_vi_du.py`](python/03_vi_du.py) | Few-shot: an `<examples>` block |
| [`04_structured_output.py`](python/04_structured_output.py) | JSON that matches a schema, with `output_config.format` |
| [`05_effort.py`](python/05_effort.py) | Compare `low` / `medium` / `high` effort |

In mock mode, the answer does not change with the prompt: the mock does not "understand" the prompt. Read the **prompt** the script prints. Run with a real key to see the difference in content.

## 1. Clear and direct

Think of Claude as a very capable colleague who just joined and does not know your habits yet. The test from the docs: give your prompt to a person who knows nothing about the task. If they are confused, Claude is too.

- State the **reader**, the **format**, the **length** and the **constraints**.
- When the order or the completeness of the steps matters, write them as a numbered list.
- If you want Claude to do more than the minimum, say so; do not expect it to guess.

## 2. Say "why", not just "what"

Compare two ways to write it:

- "NEVER use ellipses."
- "The answer will be read aloud by a speech engine, and it cannot read ellipses, so do not use them."

The second one is better. When Claude knows the reason, it works out the rules you did not write too (for example, it also avoids other symbols that are hard to read aloud). [`01_ro_rang.py`](python/01_ro_rang.py) puts the reason ("printed on a slide") in `system`.

`system` is the place for the **role** and the shared context. Even a single role sentence makes a difference.

## 3. XML tags and long documents

When a prompt mixes instructions, context, examples and data, wrap each kind in its own tag: `<instructions>`, `<context>`, `<input>`... There are no "standard" tag names. What matters is that you **use meaningful names and use them consistently**.

For long documents (about 20,000 tokens or more):

1. **Put the documents at the top**, and the question and instructions at the end. According to the docs, a question at the end can improve quality by up to 30% with multi-document input.
2. One `<document index="n">` tag per document, with `<source>` and `<document_content>` inside.

See [`02_xml_tai_lieu.py`](python/02_xml_tai_lieu.py). Exercise 1 asks you to write a function that builds this structure.

## 4. Teach with examples (few-shot)

Examples are the surest way to fix the format, the tone and the structure. According to the docs, good examples are:

- **Realistic**: like the real data you will see.
- **Varied**: they cover the edge cases. If every example has the same output, Claude learns the wrong lesson, "always answer X".
- **Structured**: each example in `<example>`, the whole set in `<examples>`.

The docs advise **3–5 examples**. [`03_vi_du.py`](python/03_vi_du.py) has one "hard" example ("Everything is fine.") to teach the label `other`.

## 5. Force a format: structured outputs instead of prefill

Old tutorials forced JSON with **prefill**: they ended `messages` with an assistant turn `"{"`. On 5.x models this returns **400**.

The replacement is **structured outputs**: pass a JSON schema in `output_config.format`, and the API makes sure the returned text matches the schema.

```python
client.create(
    messages=[...],
    output_config={"format": {"type": "json_schema", "schema": {
        "type": "object",
        "properties": {"group": {"type": "string", "enum": ["a", "b"]}},
        "required": ["group"],
        "additionalProperties": False,
    }}},
)
data = json.loads(text_of(msg))
```

Things to remember (docs: Structured outputs):

- Every `object` must have `additionalProperties: false`.
- `minimum`/`maximum`, `minLength`/`maxLength`, `multipleOf`, and `minItems` above 1 are **not** supported. To limit values, check them in code after you get the result. `claude_vi` blocks these keywords before sending.
- Trust the JSON only when `stop_reason == "end_turn"`. With `max_tokens` the JSON can be cut off; with `refusal` it may not match the schema.
- Claude **may change the case** of an `enum` value (for example `"Good"` instead of `"good"`). Match without regard to case.
- Required fields come first and optional fields after, in the order of the schema.

The Python SDK also has `client.messages.parse(..., output_format=PydanticModel)`. The repo uses dict schemas so you can see what gets sent.

Other ways to drop prefill, according to the docs:

- To drop an opening line like "Here is...", ask for that directly in `system`.
- To continue an answer that was cut off, put its last part in a **user** turn and ask Claude to continue.

## 6. Effort instead of temperature

`temperature`, `top_p` and `top_k` are gone. The new knob is `output_config.effort`: `low`, `medium`, `high`, `xhigh`, `max`.

- Effort affects **all** output tokens: the length, the number of tool calls, and the depth of thinking.
- Defaults: `medium` on Haiku 5.5 and Opus 5.5; `high` on Sonnet 5.5 and Fable 5.1.
- `low` fits simple, fast, high-volume work. `high` fits work that must follow strict instructions. Use `xhigh`/`max` only when you measure a real gain in quality.
- Effort is a **behavior signal**, not a hard token budget. `max_tokens` is the hard cap.
- `"adaptive"` is a thinking mode, **not** an effort level.

[`05_effort.py`](python/05_effort.py) compares the thinking tokens across levels (in mock mode it only shows the trend).

## 7. Split big tasks (prompt chaining)

A multi-step task (read → extract → summarize → check) often works better as several calls, one task per call, where the output of one step is the input of the next. Capstone c2 does exactly this: one turn gets the citations, one turn turns them into JSON.

## Common traps

- **Changing a prompt with no way to measure.** A test run that "looks better" is not evidence.
- **Only saying "do not do X".** Say what to do instead ("write it as flowing paragraphs" rather than "do not use markdown").
- **Rules with no reason.** Claude follows the exact words and cannot generalize.
- **Examples that are too alike**, or only 1 example.
- **The question before a long document.**
- **XML tags named at random**, a different style in each place.
- **Prefill to force JSON**, or `temperature=0` for "stability". Both return 400 on 5.x models.
- **Trusting JSON without checking `stop_reason`.**
- **Adding `minimum`/`maxLength` to a schema**, then being surprised by a 400 error.
- **Comparing enum values case-sensitively.**

## What changed with 5.x models

| Before | Now |
|---|---|
| Prefill `{"role": "assistant", "content": "{"}` to force JSON | 400. Use structured outputs (`output_config.format`) |
| Prefill `"Here is the summary:"` to drop the opening line | 400. Ask for it directly in `system` |
| `temperature=0` for a steady answer | 400. A clear prompt plus structured outputs; tune the work with `effort` |
| `output_format` (beta) | `output_config.format`, no beta header needed |
| You had to ask "be detailed" | Newer models are more concise and may skip a summary unless you ask for one |

## Exercises

```bash
CHAM="$PWD/en/modules/02-prompt-engineering/exercises" uv run pytest modules/02-prompt-engineering -q
```

| Exercise | Content |
|---|---|
| [`bai1_tai_lieu.py`](exercises/bai1_tai_lieu.py) | Build a multi-document prompt: XML, documents first, the question last |
| [`bai2_vi_du.py`](exercises/bai2_vi_du.py) | A few-shot block; check there are 3–5 examples and that they are varied |
| [`bai3_phan_loai.py`](exercises/bai3_phan_loai.py) | Classify with structured outputs; check `stop_reason`; normalize the case of enum values |

Solutions are in [`solutions/`](../../../modules/02-prompt-engineering/solutions/). Check yourself: [quiz.md](quiz.md). Sources: [references.md](references.md).

## Next

Module 03, Tool use: let Claude call your functions.
