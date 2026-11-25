# Sources · Module 09

Checked on **2026-11-25**, with `claude-agent-sdk` **0.2.189** (bundling Claude Code CLI 2.1.332). The lesson is written in this repo's own words. The English text is a translation of the Vietnamese edition; the check dates did not change. The Agent SDK docs live at `code.claude.com/docs/en/agent-sdk/`; the path `platform.claude.com/docs/en/agent-sdk/` redirects (HTTP 307) there.

| Topic | Source | Checked on | Used for |
|---|---|---|---|
| What the Agent SDK is, compared with the Client SDK, the CLI and Managed Agents; it runs the Claude Code CLI in your process; users may not log in with claude.ai unless approved; product naming rules; Commercial Terms | [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview) | 2026-11-25 | Section 1 |
| The package bundles the CLI, no Node needed (except when installed from an sdist); authentication with `ANTHROPIC_API_KEY`, `.env` not read automatically; environment variables for Bedrock, Vertex, Foundry | [Quickstart](https://code.claude.com/docs/en/agent-sdk/quickstart) | 2026-11-25 | Section 1, `claude_vi.agent_sdk` |
| Package name, version 0.2.189 (2026-11-25), Python ≥ 3.10, MIT license, wheel size about 165–178 MB | [PyPI claude-agent-sdk](https://pypi.org/project/claude-agent-sdk/) | 2026-11-25 | Section 1, why it is not a dependency |
| `query()`, `ClaudeSDKClient`, `ClaudeAgentOptions` (the fields used in the lesson), message and content block types, the 5 values of `ResultMessage.subtype`, `PermissionResultAllow`/`Deny`, `ToolPermissionContext`, `HookMatcher` (with `on_failure`), `@tool` and the 3 forms of `input_schema`, `create_sdk_mcp_server`, `AgentDefinition`, `ResultError` (since 0.2.140), `effort`/`thinking`, `max_thinking_tokens` deprecated | [Python reference](https://code.claude.com/docs/en/agent-sdk/python); source code [anthropics/claude-agent-sdk-python v0.2.189](https://github.com/anthropics/claude-agent-sdk-python/tree/v0.2.189) (`types.py`, `__init__.py`, `query.py`) | 2026-11-25 | Sections 2–8, `claude_vi.agent_sdk_mock` |
| Each `AssistantMessage` carries one block; read the whole stream; `success` can come with `is_error`; `usage` covers only the main loop; `max_turns`/`max_budget_usd` have no limit by default, how turns are counted, the cap is checked after each response; `query()` raises after an error `ResultMessage` | [Agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop) | 2026-11-25 | Sections 2, 6, scripts 01, 03 |
| The 6-step permission flow, the 6 permission modes, `allowed_tools` only pre-approves, globs in allow and deny rules, deny rules win over `bypassPermissions`, approved calls do not reach `can_use_tool`, `dontAsk` for unattended agents, the default mode since Claude Code 2.1.302, the `bypassPermissions` warning | [Permissions](https://code.claude.com/docs/en/agent-sdk/permissions) | 2026-11-25 | Section 5, script 02, exercise 2, `_duyet` in the mock |
| The 10 Python hook events, `matcher` compares only the tool name (exact name or regex), the callback signature, blocking with `permissionDecision: "deny"`, `{}` means no opinion, fail open when a callback breaks unless `on_failure="block"`, `additionalContext` and `systemMessage`, a `Write|Edit` hook does not catch writes through `Bash` | [Hooks](https://code.claude.com/docs/en/agent-sdk/hooks) | 2026-11-25 | Section 5, script 02, exercise 2 |
| Custom tools: the simple schema form makes every key required, JSON Schema is needed for `enum`; the SDK checks input against the schema before the handler (`Input validation error`, source `__init__.py`); the handler returns `content`/`is_error`; an exception becomes an error result | [Custom tools](https://code.claude.com/docs/en/agent-sdk/custom-tools) | 2026-11-25 | Section 4, `cong_cu.py`, exercise 3 |
| The name `mcp__<key>__<tool>`, the key is the key in `mcp_servers`; the wildcard `mcp__<server>__*`; an MCP tool that is not approved is visible but cannot be called | [MCP](https://code.claude.com/docs/en/agent-sdk/mcp) | 2026-11-25 | Section 4 |
| Names of the built-in tools; `Task` renamed to `Agent`; `Glob`/`Grep` missing by default on Linux, macOS, WSL | [Tools reference](https://code.claude.com/docs/en/tools-reference) | 2026-11-25 | Section 3 |
| `session_id`, `resume`, `continue_conversation`, `fork_session`, where sessions are saved, resuming on another machine | [Sessions](https://code.claude.com/docs/en/agent-sdk/sessions) | 2026-11-25 | Section 6, script 03 |
| `total_cost_usd` is a client-side estimate; deduplicate by `message_id`; `output_tokens` per step is a placeholder; a resumed or forked session already includes the earlier cost; subagents count toward `total_cost_usd` | [Cost tracking](https://code.claude.com/docs/en/agent-sdk/cost-tracking) | 2026-11-25 | Section 7, script 03, exercise 1 |
| The default system prompt is minimal; the `claude_code` preset | [Modifying system prompts](https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts) | 2026-11-25 | Section 3 |
| `setting_sources` loads every source by default; `[]` drops user/project/local, but policy, `~/.claude.json` and auto memory are still loaded (the section "What settingSources does not control"); `"project"` is needed to load `CLAUDE.md`; isolating many customers | [Claude Code features](https://code.claude.com/docs/en/agent-sdk/claude-code-features) | 2026-11-25 | Section 3 |
| Subagents: `AgentDefinition`, the `Agent` tool, a separate context, only the final message is returned | [Subagents](https://code.claude.com/docs/en/agent-sdk/subagents) | 2026-11-25 | Section 8 |
| Structured outputs in the SDK | [Structured outputs](https://code.claude.com/docs/en/agent-sdk/structured-outputs) | 2026-11-25 | Section 8 |
| One CLI process per `query()`; a suggested 1 GiB of RAM, 5 GiB of disk, 1 CPU per agent; the risk of context leaking between customers | [Hosting](https://code.claude.com/docs/en/agent-sdk/hosting) | 2026-11-25 | Sections 3, 7 |
| Prompt injection and model mistakes; several layers of defense, least privilege, credentials through a proxy | [Secure deployment](https://code.claude.com/docs/en/agent-sdk/secure-deployment) | 2026-11-25 | Section 8 |
| Claude Code SDK renamed to Claude Agent SDK in 0.1.0; `can_use_tool` works with a string prompt since 0.2.140; `on_failure` since 0.2.177 | [CHANGELOG v0.2.189](https://github.com/anthropics/claude-agent-sdk-python/blob/v0.2.189/CHANGELOG.md) | 2026-11-25 | Section 5, the "What changed" table |
| The tokenizer since the 4.7 models, `display` defaults to `"omitted"` since Opus 4.7, the `budget_tokens` rules on 5.x models | [module 06 references](../06-cost/references.md), [module 07 references](../07-thinking/references.md) | 2026-11-25, 2026-11-09 | The "What changed" table |

## Where the docs and the source code do not agree yet (noted, not used in the lesson)

- The default hook timeout: the docs say 600 seconds (30 seconds for `UserPromptSubmit`); a comment in `types.py` says 60.
- How turns are counted: the Agent loop docs count each tool-call turn plus one turn for the final answer; the `max_turns` docstring in the source code describes it differently. The lesson follows the docs.
- The `can_use_tool` example in the User input docs still uses a streaming prompt with a dummy hook as a "workaround"; CHANGELOG 0.2.140 says `can_use_tool` already works with a string prompt. The script uses a string prompt, as the CHANGELOG says; not yet checked with a real run.
- The CHANGELOG stops at 0.2.178; versions 0.2.179–0.2.189 only bump the bundled CLI version (per the commits on GitHub).

## Where the mock differs from the real SDK

- It does not run the CLI, has no built-in tools, no `ClaudeSDKClient`, no ask rules, and does not handle the `interrupt` of `PermissionResultDeny`.
- Each turn the mock calls exactly one tool; the real SDK can call several tools in one turn.
- Schema checks on input are minimal (required fields, types, `enum`); the real SDK uses `jsonschema`.
- `continue_conversation` with `resume`: the mock raises `ValueError`; the docs only say the two options exclude each other.
- The mock always fills in `usage` and `total_cost_usd`; the real SDK makes these fields `Optional`.
- The mock records calls denied by a hook in `permission_denials`; not yet checked whether the real SDK records this case.
- The token counts, the costs and the answer text are simulated; the message stream, the class names, the field names and the order of permission checks follow the docs.

## Estimated cost

3 scripts, 9 agent runs (01: 2, 02: 3, 03: 4), about 18 model turns with `claude-haiku-5-5`. Each run has a cap of `max_budget_usd=0.01` (two runs in script 03 set a very small cap on purpose), so the worst case is about $0.09 plus a small overshoot. If each turn reaches about 5,000 input tokens and 500 output tokens, the whole module is about 18 × ($0.0005 + $0.00025) ≈ $0.014. The size of the system prompt and tool definitions that the CLI sends has not been measured. This is an estimate, not yet run for real.
