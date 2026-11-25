# Sources · Module 02

Checked on **2026-10-24**. The lesson is written in this repo's own words; nothing is copied from `anthropics/courses` or `prompt-eng-interactive-tutorial` (see [NOTICE.md](../../../NOTICE.md)). The English text is a translation of the Vietnamese edition; the check dates did not change.

| Topic | Source | Used for |
|---|---|---|
| When to do prompt engineering; you need success criteria and a way to measure first | [Prompt engineering overview](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview) | "Why learn this" |
| Clear and direct, add the reason, examples (3–5, `<example>`), XML tags, roles, long documents on top and the question at the end (up to 30%), format control, dropping prefill, prompt chaining | [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) | Sections 1–5, 7 |
| `output_config.effort`, 5 levels, the default per model, effort is not a hard budget, `adaptive` is not an effort level | [Effort](https://platform.claude.com/docs/en/build-with-claude/effort) | Section 6, `config/models.yaml` (`default_effort`) |
| `output_config.format`, JSON Schema limits (`additionalProperties: false`, no `minimum`/`maxLength`..., `minItems` 0 or 1), property order, enum case may change, `messages.parse` | [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) | Section 5, exercise 3, `claude_vi.rules.schema_errors` |
| Thinking `enabled` removed since 4.7; `between_tools` only on Sonnet 5.5; `disabled`/`between_tools` do not go with effort `xhigh`/`max` | [Claude API errors](https://platform.claude.com/docs/en/api/errors) | New rules in `claude_vi.rules` |

## More resources (links only)

- [anthropics/prompt-eng-interactive-tutorial](https://github.com/anthropics/prompt-eng-interactive-tutorial): written for Claude 3, no open license yet. Read only; do not copy.
- [Metaprompt (Claude Cookbook, MIT)](https://colab.research.google.com/github/anthropics/claude-cookbooks/blob/main/misc/metaprompt.ipynb): generates a first draft of a prompt.

## Estimated cost

5 scripts, 8 calls, each with at most 1,024 output tokens on Haiku 5.5 ($0.10 / $0.50 per MTok): the worst case is about 8 × 1,024 × 0.50 / 10⁶ ≈ $0.004, plus a negligible input part.
