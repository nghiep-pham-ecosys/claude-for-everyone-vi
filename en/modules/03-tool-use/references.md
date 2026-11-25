# Sources · Module 03

Checked on **2026-10-24**. The lesson is written in this repo's own words. The English text is a translation of the Vietnamese edition; the check dates did not change.

| Topic | Source | Used for |
|---|---|---|
| Client tools and server tools; the tool use round; `disable_parallel_tool_use`; tool runner; system prompt tokens for tools (286 tokens with `auto`/`none` on Haiku/Sonnet/Opus 5.5) | [Tool use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview) | Sections 1, 3, 6 |
| `name` matches `^[a-zA-Z0-9_-]{1,128}$`; a detailed description is the most important factor (3–4 sentences); merging tools; name prefixes; `input_examples`; the `tool_choice` table; Opus 5.5/Sonnet 5.5/Fable 5.1 reject any/tool; Haiku 5.5 accepts it but drops thinking | [Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools) | Sections 2, 5, exercise 1, `claude_vi.rules.tool_errors` |
| The fields of `tool_use`/`tool_result`; `tool_result` comes right after and first in the content; `is_error` with a useful message; tool content is untrusted data | [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) | Sections 3, 6, exercise 2 |
| `strict: true` guarantees the input matches the schema; at most 20 strict tools; the same JSON Schema limits as structured outputs | [Strict tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use), [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) | Section 2 |
| A thinking block in the latest assistant turn must not be edited; a block is tied to the conversation before it | [Claude API errors](https://platform.claude.com/docs/en/api/errors), [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) | Section 4, script 05, the check in the mock |
| Designing tools for agents | [Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) | Further reading |

## Estimated cost

5 scripts, 11 calls (01: 2, 02: 2, 03: 3, 04: 2, 05: 2; one call in 05 is blocked right away in mock mode, and on the real API it also returns 400 and costs no output tokens). Worst case with Haiku 5.5: 11 × 1,024 × $0.50/MTok ≈ $0.006, plus input (about 600–1,000 tokens per call because of the tool definitions, ≈ $0.001).
