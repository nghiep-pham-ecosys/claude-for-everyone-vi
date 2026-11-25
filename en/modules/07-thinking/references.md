# Sources · Module 07

Checked on **2026-11-09**. The lesson is written in this repo's own words. The English text is a translation of the Vietnamese edition; the check dates did not change.

| Topic | Source | Used for |
|---|---|---|
| What thinking is, `signature`, billed as output tokens and counted toward `max_tokens`; the setup table by model (`adaptive`/`enabled`/`between_tools`/`disabled`); `display` (`summarized`, `omitted`, `updates` beta), the summary is written by another model and billed by the original thinking; `reasoning_extraction`; streaming (`thinking_delta`, `signature_delta`, `get_final_message`); thinking with tools (one assistant turn, keep the blocks, no setting changes within a turn, interleaved, progress updates); which models keep blocks; `redacted_thinking`; output limits; the SDK requires streaming when `max_tokens` > 21,333 | [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) | Sections 1–6, scripts 01–04, the `display`/`between_tools` rules in `claude_vi.rules` |
| 5 effort levels, the default of each model (Fable 5.2 included), effort affects every output token and is not a hard budget, effort per message (beta), changing effort breaks the cache | [Effort](https://platform.claude.com/docs/en/build-with-claude/effort) | Section 4 |
| The prefix check (system, tools, messages before the block); the error table by model and account creation date (2026-08-31); the 400 error message; `block_binding` (beta); what counts as changing the prefix and what to do instead; dropping the oldest blocks is allowed, dropping one in the middle breaks things; blocks are bound to an account | [Preserved thinking](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking) | Section 7, script 05, exercise 3, `_check_prefix` in the mock |
| A `role: "system"` message mid-conversation: supported models, no beta header needed, position rules, no outside data in it | [Mid-conversation system messages](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages) | Section 7, `claude_vi.rules.system_message_errors` |
| Common 400 errors about thinking | [Troubleshooting thinking](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting) | Common traps |
| Claude Fable 5.2 launch: price $8/$40 per MTok, adaptive thinking always on, prefix check for every account, blocks bound to an account | [Release notes 2026-11-09](https://platform.claude.com/docs/en/release-notes/overview), [Fable 5.2 migration guide](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide) | `config/models.yaml`, the table in section 3 |

## Estimated cost

5 scripts, 11 calls to the default model (01: 2, 02: 1, 03: 4, of which 3 calls have `max_tokens` ≤ 16, 04: 1, 05: 3). Script 02 checks the other models on your machine and sends no request. Worst-case output with Haiku 5.5: 8 × 1,024 × $0.50/MTok ≈ $0.004; the input is negligible. The whole module costs under $0.01. This is an estimate, not yet measured with the real API.

Script 05 sends a wrong request on purpose. On an account created on or after 2026-08-31 it returns 400 and costs no output tokens.
