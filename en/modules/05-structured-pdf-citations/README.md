# 05 · Structured outputs, PDF and Citations

**Type:** Learn + Build · **Time:** about 2.5 hours · **Needs:** modules 01–02 · **Cost:** $0 in mock mode; under $0.01 if you run it for real with `claude-haiku-5-5` (prices checked 2026-10-24, see [references.md](references.md))

## Goals

After this module you can:

- Write a schema with Pydantic, send it through structured outputs, and still keep the constraints (`ge`, `le`) on the code side.
- Know the limits of JSON Schema in structured outputs, including the complexity limits counted across the whole request.
- Send a PDF to Claude in three ways, and estimate the cost.
- Turn on citations for plain text, PDF and custom content, and read the three kinds of citation location correctly.
- Check on your own that a citation points to the right place in the document.
- Get structured data **with citations**, even though citations and structured outputs cannot be used together.

| Learn | Build |
|---|---|
| Read sections 1–6 and run the 5 scripts in `python/` | Do the 3 exercises in `exercises/`, then do [capstone c2](../../../capstones/c2-trich-xuat-pdf) |

## Why learn this

Most real applications do not need Claude to "chat". They need Claude to **read documents and return data** that code can use right away: a table of numbers, a filled-in form, an answer with sources.

Two questions always come with it:

1. **Is the data in the right format?** Structured outputs answer this one: the API makes sure the JSON matches the schema.
2. **Where does the data come from?** Citations answer this one: the API returns the real location in the document, not a claim the model makes up.

Neither one replaces the other. JSON that matches the schema can still hold made-up numbers. A correct quote can still be tied to the wrong quantity. This module teaches you to use both, and then to **check again in code**.

## The minimum that runs

```bash
CLAUDE_MOCK=1 uv run python en/modules/05-structured-pdf-citations/python/03_citations_van_ban.py
```

| Script | Main idea |
|---|---|
| [`01_pydantic_schema.py`](python/01_pydantic_schema.py) | Pydantic schema → `transform_schema` → send; check the constraints when you read the result |
| [`02_pdf.py`](python/02_pdf.py) | Send a base64 PDF; estimate the tokens; the URL and Files API ways |
| [`03_citations_van_ban.py`](python/03_citations_van_ban.py) | Citations on plain text, check `char_location` |
| [`04_custom_content.py`](python/04_custom_content.py) | Custom content: each block is one citation unit |
| [`05_truong_kem_trich_dan.py`](python/05_truong_kem_trich_dan.py) | Get each field with a citation, without structured outputs |

In mock mode, citations are "half real": the mock reads the document you send (PDFs too) and quotes the sentences that hold at least 2 numbers, with the right location. The mock does not understand the question, so it does not pick sentences by meaning. Structured outputs in mock mode return the smallest value the schema allows (`"[MOCK]"`, `0`, the first item of an `enum`).

## 1. Structured outputs, a recap and a deeper look

Module 02 taught `output_config.format`. Three things to remember:

- Every `object` needs `additionalProperties: false`.
- Trust the JSON only when `stop_reason == "end_turn"`. With `max_tokens` the JSON can be cut off; with `refusal` it may not match the schema.
- Claude can change the case of an `enum` value. Compare without case.

### Writing the schema with Pydantic

A schema dict written by hand is long and easy to get wrong. A shorter way is to declare a Pydantic class, and let the SDK turn it into a schema you can send:

```python
from anthropic import transform_schema

class PhepDo(BaseModel):            # "phep do" = a measurement
    mau: str                        # sample
    gia_tri: float = Field(ge=0)    # value

schema = transform_schema(PhepDo)   # adds additionalProperties: false, drops "minimum"
```

`transform_schema` does three main things: it adds `additionalProperties: false` to every object, it **drops** the constraints the API does not support (`minimum`, `maximum`, `minLength`...), and it copies them into the `description` (for example `{minimum: 0}`) so Claude can still read them.

**Why you still have to check in code:** once `minimum` is dropped, the API no longer makes sure that `gia_tri >= 0`. It only makes sure that `gia_tri` is a number. Read the result with `PhepDo.model_validate_json(...)`: Pydantic checks the original constraints again. If you send `PhepDo.model_json_schema()` as it is, the schema still has `minimum` and lacks `additionalProperties`, so the API returns 400 (`claude_vi` stops it first).

The SDK also has `client.messages.parse(..., output_format=PhepDo)`, which does both steps. The repo uses a dict so you can see clearly what is sent.

### What a schema cannot do

| Not supported | Do this instead |
|---|---|
| `minimum`/`maximum`, `multipleOf` | Check in code (Pydantic) |
| `minLength`/`maxLength` | Check in code |
| `minItems` greater than 1 | Check in code |
| Recursive schemas | Flatten the structure |
| `pattern` with backreferences (`\1`), lookahead/lookbehind, `\b` | A simpler regex, or check in code |

### Complexity limits

Structured outputs compile the schema into a grammar that forces the output. The more complex the schema, the longer it takes to compile. So the API sets limits **counted across every strict schema in one request** (`output_config.format` plus every tool with `strict: true`):

| Limit | Value |
|---|---|
| Strict tools | 20 |
| Optional parameters (not in `required`) | 24 |
| Parameters that use a union (`anyOf`, or a `type` that is a list such as `["string", "null"]`) | 16 |

If you go over other, hidden limits, you get a 400 "Schema is too complex for compilation". Ways to cut it down, in order: set strict only on the tools that really need it; move parameters into `required` when they have a sensible default; flatten nested objects; split into several requests.

Note: in Pydantic, `ghi_chu: str | None = None` ("ghi chu" = note) is optional **and** a union, so it counts toward both limits. `claude_vi` counts these two numbers and stops the request before it is sent.

The first time you use a schema, the request is slower because the schema must be compiled. The compiled version is cached for 24 hours from its last use. Changing the structure of the schema loses the cache; changing only `name`/`description` does not.

## 2. PDF

**How the API reads a PDF:** each page is turned into an image, and the text of the page is extracted and sent along. Claude reads both, so it understands tables, charts and drawings. What this means for cost: each page costs text tokens (usually 1,500–3,000 tokens, depending on how dense it is) **plus** image tokens. There is no separate fee for PDFs. For an exact number, use token counting (module 06).

Three ways to put a PDF in a `document` block:

| Source | When to use it |
|---|---|
| `{"type": "base64", "media_type": "application/pdf", "data": ...}` | A file on your machine, used once. Script 02 and capstone c2 use this way |
| `{"type": "url", "url": "https://..."}` | A public PDF on the web |
| `{"type": "file", "file_id": "file_..."}` | Upload once through the Files API, reuse it in many requests; keeps each request small |

Limits (checked 2026-11-09): a request is at most **128 MB** on the Claude API, and at most **600 pages** (100 pages if the request's context window is under 1 million tokens). The PDF must not have a password. A dense PDF can fill the context before it reaches the page limit; then split the PDF into several parts.

Tips from the docs: put the PDF **before** the question; when you mention a page, use the page number shown in the PDF reader; rotate pages so they are upright.

## 3. Citations: how they work

Turn on `citations: {"enabled": true}` on a `document` block. The API does three things:

1. **It cuts the document into citation units.** Plain text and PDFs are cut into sentences. Custom content keeps each block you give it as it is.
2. **Claude answers** in several `text` blocks. A block that holds a claim with a source has a `citations` list.
3. **The API fills in `cited_text` itself** from the original document, so a citation always points to text that really exists.

```text
content = [
  text("According to the form, "),
  text("sample W2 has pH 6.4", citations=[char_location(cited_text="Sample W2 has ... pH 6.4.", 93, 127)]),
  text(" so it is below 7."),
]
```

The cost benefit: `cited_text` does **not** count as output tokens, and when you send it back in a later turn it does not count as input tokens either. Turning on citations costs a few extra input tokens (the system prompt and the cutting of the document).

Rules to know:

- Turn on citations for **all or none** of the documents in a request. If you mix them, `claude_vi` stops the request.
- `title` and `context` are sent to Claude but are **never** cited. Use `context` for metadata (for example, JSON that describes the source).
- Only text can be cited. A scanned PDF with no text layer cannot be cited.
- Streaming: a citation arrives as a `citations_delta`, one citation per delta, to attach to the text block being streamed.
- Works with prompt caching (put `cache_control` on the document block), token counting and batches.

## 4. The three kinds of citation location

| Document type | `source` | Cut into | Citation type | Index |
|---|---|---|---|---|
| Plain text | `{"type": "text", "media_type": "text/plain", "data": ...}` | Sentences | `char_location` | Characters, **from 0**, end excluded |
| PDF | base64 / URL / file | Sentences | `page_location` | Pages, **from 1**, end excluded |
| Custom content | `{"type": "content", "content": [blocks...]}` | Not cut further | `content_block_location` | Blocks, **from 0**, end excluded |

`document_index` counts from 0 across **every** document block in the request, through every message turn.

"End excluded" means a sentence that sits fully on page 1 has `start_page_number=1, end_page_number=2`. For plain text, `data[start:end] == cited_text`, exactly like a Python slice. [`03_citations_van_ban.py`](python/03_citations_van_ban.py) checks exactly this.

**When to use custom content:** bullet lists, transcripts, machine logs, RAG chunks you have cut yourself. Cutting these into sentences easily gives meaningless pieces. With RAG (module 04): if you want Claude to cite single sentences inside a chunk, make each chunk a plain text document; if you want it to cite whole chunks, put the chunks in one custom content document.

## 5. Citations and structured outputs do not go together

If citations are on for any document **and** the request has `output_config.format`, the API returns 400. The reason: citations must insert cited blocks in the middle of the text, while structured outputs force the text to be exactly one JSON.

There are two ways to get structured data with sources:

**Way A: two turns** (capstone c2). Turn 1 turns on citations to get the quotes and their locations. Turn 2 sends the list of quotes (not the PDF again) with structured outputs, and each JSON row points back to a quote id through an `enum`. Good when you need a table with many rows and a strict schema.

**Way B: one turn, one line per field** (exercise 3, following the docs). Ask Claude to answer each field on its own line as `name: value` and to cite a source for each line. Then split it yourself in code:

1. Read the text blocks in order and append them to the current line; on a line break, start a new line.
2. Attach the citations of a block to every line that holds part of that block's text.
3. Drop lines with no colon; split at the **first** colon; drop lines with an unknown name.
4. Check that each field has a value and at least one citation. The API does not promise this.

Good when you only need a few flat fields. It is cheaper, with one turn.

Do not write "return only JSON, nothing else" in the prompt when citations are on: the request still succeeds, but it may have almost no citations.

## 6. Checking citations yourself

The API makes sure a citation points into the document you sent. Still, check it again in code when:

- you store citation locations for display (a highlight, a link to a page) and need to be sure the indexes follow the right convention;
- the response goes through a cache, a log or a fixture before it reaches you;
- you join citations with other data (like step 3 of capstone c2).

How to check each kind is in exercise 2. The more important point: **a citation only proves that the quote really exists in the document**. It does not prove that Claude understood that quote correctly. To be stricter, also compare the values (capstone c2 checks that the number is inside the quote), or have a person review.

## Common traps

- **Turning on citations and `output_config.format` at the same time** → 400.
- **Sending `model_json_schema()` straight to the API** → 400, because it still has `minimum` and lacks `additionalProperties`. Use `transform_schema`.
- **Using `transform_schema` and then forgetting to check the constraints.** The API no longer guarantees `ge`/`le`.
- **Many `str | None` fields** across many strict tools, which together go over 24 optional or 16 union parameters.
- **Mixing up the index conventions:** pages count from 1, characters and blocks count from 0; the end is always excluded.
- **Trusting a page number the model wrote in its text** instead of the citation's `start_page_number`.
- **Turning on citations for some documents and not for others.**
- **Putting the content you want cited in `title`/`context`.** These two fields are never cited.
- **A "return only JSON" prompt with citations on** → you lose almost all citations.
- **Sending a scanned PDF with no text layer** and waiting for citations.
- **Sending the PDF again in every turn.** Each time you pay for the tokens of the whole PDF again; use prompt caching (module 06) or send only the quoted parts.

## What changed with 5.x models

| Before | Now |
|---|---|
| Prefill `{` to force JSON | 400. Use `output_config.format` |
| `output_format` (beta, needs a beta header) | `output_config.format`, no header needed. Python SDK ≥1.0 raises `TypeError` if you pass `output_format={...}` to `client.beta.messages.create()` |
| Force JSON through tool use with `tool_choice` `tool` | 400 on Opus 5.5, Sonnet 5.5, Fable 5.1. Use structured outputs |
| Ask the model to write "(page 3)" in its answer | Citations return a location the API computes, and `cited_text` costs no output tokens |
| A request is at most 32 MB | 128 MB on the Claude API (since 2026-10-28) |

## Exercises

```bash
CHAM="$PWD/en/modules/05-structured-pdf-citations/exercises" uv run pytest modules/05-structured-pdf-citations -q
```

| Exercise | Content |
|---|---|
| [`bai1_phieu_nuoc.py`](exercises/bai1_phieu_nuoc.py) | A Pydantic schema with constraints; `transform_schema`; check again on read; normalize the enum |
| [`bai2_kiem_trich_dan.py`](exercises/bai2_kiem_trich_dan.py) | Read and check `char_location`, `page_location`, `content_block_location` yourself |
| [`bai3_truong_kem_trich_dan.py`](exercises/bai3_truong_kem_trich_dan.py) | One line per field with citations; a parser that follows the algorithm in the docs |

Solutions are in [`solutions/`](../../../modules/05-structured-pdf-citations/solutions/). Check yourself: [quiz.md](quiz.md). Sources: [references.md](references.md).

## Next

[Capstone c2](../../../capstones/c2-trich-xuat-pdf): it puts everything in this module together into a pipeline that pulls a table of numbers out of a PDF, where every number traces back to its source page. After that comes module 07, Thinking.
