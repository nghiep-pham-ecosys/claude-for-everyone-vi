# Sources · Module 05

Checked on **2026-11-09**. The lesson is written in this repo's own words. The English text is a translation of the Vietnamese edition; the check dates did not change.

| Topic | Source | Used for |
|---|---|---|
| `output_config.format`; JSON Schema limits (no `minimum`/`maxLength`/recursion, `minItems` 0 or 1, regex with no backreference/lookaround/`\b`); property order; refusal, `max_tokens`, enum case changes; limits of 20 strict tools / 24 optional / 16 union counted across the request; "Schema is too complex for compilation"; compiled grammar cached for 24 hours; SDK transformation (drops constraints, copies them into the description, adds `additionalProperties`); `output_format` removed | [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) | Section 1, exercise 1, `claude_vi.rules.complexity_errors` and the `pattern` check |
| PDF pages turned into image + text; 1,500–3,000 text tokens per page plus image tokens; base64 / URL / Files API; 128 MB; 600 pages (100 if the context is under 1M); put the PDF before the text | [PDF support](https://platform.claude.com/docs/en/build-with-claude/pdf-support) | Section 2, script 02 |
| Cutting into sentences / custom content; on for all or none; `title`/`context` never cited; indexes (characters from 0, pages from 1, blocks from 0, end excluded); `cited_text` not counted as tokens; `citations_delta`; cannot be used with structured outputs; the "one line per field" way and its 4 parsing steps; avoid "return only JSON" prompts | [Citations](https://platform.claude.com/docs/en/build-with-claude/citations) | Sections 3–6, exercise 2, exercise 3, mock custom content and streamed citations |
| Request size limit 32 → 128 MB | [Release notes 2026-10-28](https://platform.claude.com/docs/en/release-notes/overview) | "What changed" |
| `anthropic.transform_schema`, `messages.parse(output_format=...)` | `anthropic` Python SDK 1.17.0 (read from the installed source code) | Section 1, script 01, exercise 1 |

## Estimated cost

5 scripts, 5 calls (the first call in script 05 is stopped on your machine; with the real API it also returns 400). Worst-case output with Haiku 5.5: 5 × 1,024 × $0.50/MTok ≈ $0.003. Input: the 2-page sample PDF is a few thousand text tokens plus image tokens, and the other scripts are under 1,000 tokens; total input under 20,000 tokens ≈ $0.002. The whole module costs under $0.01. This is an estimate, not yet measured with the real API.
