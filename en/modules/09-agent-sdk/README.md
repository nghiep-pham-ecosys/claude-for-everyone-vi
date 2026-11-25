# 09 · Agent SDK

**Type:** Learn + Build · **Time:** about 2 hours · **Needs:** modules 03, 06, 07 and 08 · **Cost:** $0 in mock mode; when you run it for real, each agent run has a cap of `max_budget_usd=0.01`, and the whole module is estimated at about $0.02 (not measured, see [references.md](references.md))

## Goals

After this module you can:

- Say what the Agent SDK is, how it differs from the Client SDK (`anthropic`, the earlier modules), and when to use it.
- Run an agent with `query()` and read the message stream the right way: `SystemMessage` → `AssistantMessage` / `UserMessage` → `ResultMessage`.
- Write your own tools with `@tool` and `create_sdk_mcp_server`, and call them by the right name, `mcp__<server>__<tool>`.
- Decide which tools may run with `allowed_tools`, `disallowed_tools`, `permission_mode`, `can_use_tool` and the `PreToolUse` hook, in the order the SDK checks them.
- Set the caps `max_turns` and `max_budget_usd`, handle `ResultError`, and continue a session with `resume`.
- Read the cost of a run without counting anything twice.

| Learn | Build |
|---|---|
| Read sections 1–8 and run the 3 scripts in `python/` | Do the 3 exercises in `exercises/`, graded by tests |

## Why learn this

In module 08 you wrote the agent loop yourself: send a request, read `stop_reason`, run the tool, send `tool_result`, count the turns, add up the cost, block dangerous tools. The **Agent SDK** does most of that for you. It is a library that runs the same loop, the same tools and the same context management as Claude Code, and you can call it from Python or TypeScript.

The price is that the loop is hidden. Mistakes are harder to see: a tool runs when you thought you had blocked it, a run has no cost cap, an agent reads a config file on your machine without you knowing. This module teaches those controls.

## The minimum that runs

```bash
CLAUDE_MOCK=1 uv run python en/modules/09-agent-sdk/python/01_query_dau_tien.py
```

| Script | Main idea |
|---|---|
| [`01_query_dau_tien.py`](python/01_query_dau_tien.py) | `query()`, read the whole message stream, `ResultMessage` (number of turns, estimated cost, the answer) |
| [`02_quyen_va_hook.py`](python/02_quyen_va_hook.py) | `allowed_tools`, `can_use_tool` (with `updated_input`), a `PreToolUse` hook that blocks by content |
| [`03_gioi_han_va_phien.py`](python/03_gioi_han_va_phien.py) | `max_turns`, `max_budget_usd`, `ResultError`, `resume` and the cost of a resumed session |

[`cong_cu.py`](python/cong_cu.py) ("tools") holds the shared parts: the two tools of a fictional lab assistant (`tra_lich`, "check the schedule", is read only; `ghi_nhat_ky`, "write to the log", has a side effect) and `options_co_ban()` ("basic options"). The tool names stay in Vietnamese because the exercises and their tests use them.

**About the mock in this module.** The `claude-agent-sdk` package is not a dependency of the repo: each wheel is about 165–178 MB because it bundles the Claude Code CLI. In mock mode, `claude_vi.agent_sdk.nap_sdk()` returns `claude_vi.agent_sdk_mock`, which has the same class names and field names as the real SDK (version 0.2.189) for the parts this lesson uses. The mock does not run the CLI and has no built-in tools. Each turn it calls **one** custom tool that has not been called yet, in the order of `mcp_servers`, and then answers. The tool input: an `enum` value that matches a keyword in the prompt; for a free-text string, the prompt itself. The real SDK can call several tools in one turn; the mock always calls one. The token counts and costs come from the mock; the prices are read from [`config/models.yaml`](../../../config/models.yaml).

To run it for real (costs API money, optional): `uv pip install claude-agent-sdk`, set `ANTHROPIC_API_KEY`, and drop `CLAUDE_MOCK=1`.

## 1. Agent SDK, Client SDK or Claude Code

| | Client SDK (`anthropic`) | Agent SDK (`claude-agent-sdk`) |
|---|---|---|
| Tool loop | You write it (modules 03, 08) | The SDK runs it for you |
| Built-in tools | No (except server tools) | Yes: read/edit files, run commands, search the web... |
| Where it runs | Calls the API directly | Runs the Claude Code CLI as a child process of your program |
| Good for | One call, a workflow you control step by step | An agent that needs to read files, run commands, do many steps |

What to know before you use it (Agent SDK docs, checked 2026-11-25):

- The Python package: `claude-agent-sdk`, latest version 0.2.189 (2026-11-25), needs Python 3.10 or later. The package bundles the Claude Code CLI (version 0.2.189 bundles CLI 2.1.332), so you do not need to install Node.
- Authentication is with `ANTHROPIC_API_KEY`. The SDK does **not** read a `.env` file by itself (`claude_vi` loads `.env` into environment variables for you). Cloud providers are turned on with environment variables: Amazon Bedrock (`CLAUDE_CODE_USE_BEDROCK=1`), Google Cloud's Agent Platform (`CLAUDE_CODE_USE_VERTEX=1`), Microsoft Foundry (`CLAUDE_CODE_USE_FOUNDRY=1`), Claude Platform on AWS.
- Third-party products may **not** let users log in with a claude.ai account or use claude.ai usage limits, unless Anthropic has approved it. Use an API key. Using the SDK falls under Anthropic's Commercial Terms.
- Product names: "Claude Agent" or "<Your name> Powered by Claude" are allowed; "Claude Code", or a look like Claude Code, is not.
- The Agent SDK docs moved from `platform.claude.com/docs/en/agent-sdk/` to `code.claude.com/docs/en/agent-sdk/` (the old path redirects to the new one).

## 2. `query()` and the message stream

```python
async for msg in sdk.query(prompt="Is the HV-200 free this afternoon?", options=options):
    if isinstance(msg, sdk.ResultMessage):
        print(msg.subtype, msg.num_turns, msg.total_cost_usd, msg.result)
```

`query()` returns an async iterator. Each call is a **new session**, unless you `resume` (section 6). For a multi-turn conversation in one process, with interrupts, use `ClaudeSDKClient` (the repo has no mock for this class yet).

The message types:

| Message | Main content |
|---|---|
| `SystemMessage`, `subtype="init"` | `data` has `session_id`, `model`, `tools`, `mcp_servers`, `permissionMode` |
| `AssistantMessage` | `content`: `TextBlock`, `ThinkingBlock`, `ToolUseBlock`. **Each message carries one block**; the blocks of one response share the same `message_id` |
| `UserMessage` | `ToolResultBlock`: the tool results the SDK sends back to Claude |
| `ResultMessage` | `subtype`, `is_error`, `num_turns`, `session_id`, `total_cost_usd`, `usage`, `result`, `permission_denials` |

`ResultMessage.subtype` has 5 values: `success`, `error_during_execution`, `error_max_turns`, `error_max_budget_usd`, `error_max_structured_output_retries`. `result` is set only on `success`. A `success` can still come with `is_error=True`: the model refused (`stop_reason="refusal"`), a deferred tool can no longer be used, or the last request had an API error (see `terminal_reason`, `api_error_status`). Check both.

`permission_denials` lists the calls that were denied. The mock also records calls blocked by a hook; the repo has not checked whether the real SDK records this case, so exercise 1 counts errors with `ToolResultBlock.is_error`.

**Read the whole stream.** Do not `break` when you get `ResultMessage`: some system messages can come after it.

## 3. System prompt, settings and built-in tools

Three defaults that can surprise you:

- **The default system prompt is a minimal one**, not the system prompt of Claude Code (and it lacks the safety instructions of the `claude_code` preset). For Claude Code behavior: `system_prompt={"type": "preset", "preset": "claude_code", "append": "..."}`.
- **By default `setting_sources` loads every settings source** (user, project, local), including the project's `CLAUDE.md` and the one in `~/.claude`. Your agent can follow instructions from files on your machine. `setting_sources=[]` drops these three sources, but it does **not** isolate fully: policy set by an administrator, `~/.claude.json` and auto memory (`~/.claude/projects/<project>/memory/`) are still loaded. In a container that serves many customers, the docs advise: one filesystem per customer, `setting_sources=[]` and the environment variable `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`.
- **Built-in tools are on by default.** `tools=[]` turns all of them off; `tools=["Read", "Grep"]` turns on only a few. The names of built-in tools (used in permission rules and hooks): `Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`, `WebFetch`, `WebSearch`, `Agent` (old name `Task`), and many others. On Linux, macOS and WSL, `Glob` and `Grep` are missing by default (Claude searches with `find`/`grep` through `Bash`). They come back when you name them in `tools` or `allowed_tools` (one name in `allowed_tools` brings back both), or when you remove `Bash` (for example `disallowed_tools=["Bash"]`).

That is why `options_co_ban()` in `cong_cu.py` sets `tools=[]`, `setting_sources=[]`, `max_turns=5`, `max_budget_usd=0.01`.

## 4. Custom tools

```python
@sdk.tool("tra_lich", "Check the bookings of one device.", {
    "type": "object",
    "properties": {"ma_thiet_bi": {"type": "string", "enum": ["HV-200", "LN-1200", "QS-3"]}},
    "required": ["ma_thiet_bi"],
})
async def tra_lich(args):
    return {"content": [{"type": "text", "text": "HV-200: free in the afternoon."}]}

server = sdk.create_sdk_mcp_server(name="phong-thi-nghiem", version="1.0.0", tools=[tra_lich])
options = sdk.ClaudeAgentOptions(mcp_servers={"ptn": server}, allowed_tools=["mcp__ptn__tra_lich"])
```

(`ma_thiet_bi` = device code, `phong-thi-nghiem` = lab, `ptn` is its short form.)

- `input_schema` comes in three forms: the simple form `{"ma_thiet_bi": str}` (every key is required), a full JSON Schema, or a `TypedDict` class. For an `enum`, an optional field or a value range, use JSON Schema.
- The SDK checks the input against `input_schema` **before** it calls the handler. Input that breaks the schema (a missing field, a wrong type, a value outside the `enum`) returns `Input validation error` to Claude, and the handler does not run. Errors in the handler are for what the schema cannot express (values known only at run time).
- The handler is an async function that takes **one** dict. It returns `{"content": [...]}`, plus `"is_error": True` on an error. An exception in the handler also becomes an error result sent to Claude. Write useful error messages as in module 08: what is wrong, which values are valid.
- The full name is `mcp__<key in mcp_servers>__<tool name>`. The key is `"ptn"`, not the `name` of `create_sdk_mcp_server`.
- The server runs **inside** your process; it needs no separate process.

## 5. Who may run which tool

When Claude wants to call a tool, the SDK checks in this order (docs Permissions):

1. **Hook** `PreToolUse`: can allow, deny, or have no opinion.
2. **Deny rules** (`disallowed_tools`): win over everything, even `bypassPermissions`, and even when a hook has allowed the call.
3. **Ask rules**.
4. **`permission_mode`**: `default`, `acceptEdits`, `plan`, `bypassPermissions`, `dontAsk`, `auto`.
5. **Allow rules** (`allowed_tools`).
6. **`can_use_tool`**: your callback. In `dontAsk` this step is skipped and the call is denied.

What follows from this:

- **`allowed_tools` is a pre-approval list, not a limit list.** A tool that is not in it still exists and goes on to `permission_mode` and `can_use_tool`. To remove a tool fully: put its bare name in `disallowed_tools`, or leave it out of `tools`.
- Globs in rules: `mcp__ptn__*` approves every tool of one server; `*` or `mcp__*` in `allowed_tools` is **ignored**. In `disallowed_tools`, `*` blocks every tool and `mcp__*` blocks every MCP tool.
- **A call already approved at an earlier step does not reach `can_use_tool`.** To see every call, use a `PreToolUse` hook. The SDK warns you when you register `can_use_tool` together with `allowed_tools` or `bypassPermissions`.
- For an agent that runs unattended: use `allowed_tools` with `permission_mode="dontAsk"`. In the default mode (Claude Code since 2.1.302), a call that needs approval and gets none is denied.
- **`bypassPermissions`** gives Claude full control of the machine. In this mode `allowed_tools` limits nothing at all. Subagents inherit this mode too.

`can_use_tool` (script 02, exercise 2):

```python
async def can_use_tool(tool_name, input_data, context):
    if tool_name == "mcp__ptn__ghi_nhat_ky" and len(input_data["noi_dung"]) <= 200:
        return sdk.PermissionResultAllow(updated_input={"noi_dung": "[agent] " + input_data["noi_dung"]})
    return sdk.PermissionResultDeny(message="Not approved: the text is too long.")
```

Hook (script 02, exercise 2):

```python
async def block_delete(input_data, tool_use_id, context):
    if "delete" in str(input_data["tool_input"]).lower():
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                       "permissionDecisionReason": "The log is append only."}}
    return {}   # no opinion

hooks = {"PreToolUse": [sdk.HookMatcher(matcher="^mcp__ptn__", hooks=[block_delete])]}
```

- `matcher` is compared only with the tool **name**, never with its arguments. A matcher made only of letters, digits, `_` and `|` is an exact name (`"mcp__ptn__ghi_nhat_ky"`, or a list such as `"Write|Edit"`); anything else is a regex (`"^mcp__ptn__"`). `"ghi_nhat_ky"` does **not** match `mcp__ptn__ghi_nhat_ky`. Filtering by content must happen in the callback.
- Python has 10 hook events: `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `UserPromptSubmit`, `Stop`, `SubagentStop`, `PreCompact`, `Notification`, `SubagentStart`, `PermissionRequest`. `SessionStart` and `SessionEnd` are not in Python.
- If a callback fails (raises an exception), by default the call goes on as if there were no hook: it **fails open**. Set `on_failure="block"` in `HookMatcher` to block when the hook breaks; then a callback that returns `None` also counts as broken, so to say "no opinion" return `{}`.
- `additionalContext` in `hookSpecificOutput` reaches Claude; `systemMessage` is shown only to the user.
- A hook for `Write|Edit` does not catch files written through `Bash`.

## 6. Limits, errors and sessions

- `max_turns` and `max_budget_usd` have **no limit** by default. Each turn with tool calls counts as one turn, whether Claude calls one tool or many in parallel in that turn; the final answer adds one more turn.
- `max_budget_usd` is based on a client-side cost estimate and is checked **after** each response, so a run can go slightly over the cap. It counts only the cost of this call, not the earlier part of a resumed session.
- When a limit is hit: `ResultMessage` has the `subtype` `error_max_turns` or `error_max_budget_usd`, then `query()` raises `ResultError` (since SDK 0.2.140). **Every** error result does this, including `subtype="success"` with `is_error=True`. So always wrap the `async for` loop in a `try`, as `doc_het()` in `cong_cu.py` does. `ResultError` has `subtype`, `errors`, `session_id`, `data`; the docs advise to classify by `data["stop_reason"]`, then `terminal_reason`, then `subtype`.
- **Sessions.** `session_id` is in the init `SystemMessage` and in `ResultMessage`. `resume=<id>` continues that session; add `fork_session=True` to branch off to a new id and leave the original session as it was. `continue_conversation=True` continues the latest session in the folder; do not use it together with `resume`. Sessions are saved as JSONL files on the machine (`~/.claude/projects/...`): to resume on another machine, use `session_store`, or copy the session's JSONL file into `~/.claude/projects/` on that machine.

## 7. Cost

- `ResultMessage.total_cost_usd` is a **client-side estimate**, not a bill. Do not charge your users by this number.
- The `usage` of `ResultMessage` covers only the main loop; `total_cost_usd` and `model_usage` include subagents too. These fields are `Optional`: check for `None`.
- A resumed session: `total_cost_usd` **already includes** the cost of the earlier runs. Adding up the results of two runs of the same session counts it twice (script 03, part 4).
- To count step by step with `AssistantMessage.usage`, deduplicate by `message_id`: the blocks of one response (for example several tools called in parallel) share the same id. The input and cache numbers per step are usable; `output_tokens` per step is only a placeholder, so read the total output from `ResultMessage.usage`.
- Each `query()` runs one CLI process. When you package agents in containers, the docs suggest starting with 1 GiB of RAM, 5 GiB of disk and 1 CPU per agent.

## 8. Other features (introduction only)

- **Subagents:** `agents={"name": sdk.AgentDefinition(description=..., prompt=..., tools=[...], model="haiku")}`. Claude hands work over through the `Agent` tool. A subagent (except a fork) starts with **none of the main agent's conversation**; its context is not empty (its system prompt, tools, `CLAUDE.md`), but the only thing passed to it is the prompt string of the `Agent` tool. It returns only its final message. Its cost counts toward `total_cost_usd`. Multi-word fields of `AgentDefinition` are written in camelCase (`disallowedTools`, `maxTurns`).
- **Structured outputs:** `output_format={"type": "json_schema", "schema": {...}}`, then read `ResultMessage.structured_output`. A `success` does not always have output: check `is_error` and this field.
- **Thinking and effort:** `effort="low"` to `"max"`; `thinking={"type": "adaptive", "display": "summarized"}` to read a summary of the thinking. `max_thinking_tokens` is deprecated.
- **Safety:** the docs name two sources of unwanted actions: prompt injection and model mistakes. Use several layers of defense: least privilege, a sandbox, and credentials passed through a proxy instead of letting the agent read them.

## Common traps

- **Thinking `allowed_tools` is a limit list.** It only pre-approves. Use `tools`/`disallowed_tools` to remove tools.
- **Thinking `can_use_tool` sees every call.** Calls that are already approved never reach it. Use a `PreToolUse` hook.
- **Not setting `max_turns` and `max_budget_usd`.** By default there is no limit.
- **Letting the agent load the `CLAUDE.md` and settings of your machine.** Set `setting_sources=[]` when you do not need them, and remember that it does not isolate fully (section 3).
- **Writing the tool name wrong.** The right form is `mcp__<key in mcp_servers>__<tool>`. `mcp__*` in `allowed_tools` approves nothing.
- **Filtering by arguments with `matcher`, or writing part of a name as the matcher.** `matcher` compares only the tool name; a string of only letters, digits and `_` is an exact name.
- **A hook raises an exception and you think the call was blocked.** By default it fails open; use `on_failure="block"`.
- **`break` out of the stream as soon as you get `ResultMessage`**, or thinking one `AssistantMessage` holds the whole response.
- **Adding up `total_cost_usd` of resumed runs of the same session.** The later number already includes the earlier one.
- **Treating `total_cost_usd` as a bill.** It is an estimate.
- **Using `bypassPermissions` because it is convenient.** Claude gets full control of the machine, and so do subagents.

## What changed with 5.x models

| Before | Now |
|---|---|
| Claude Code SDK, `ClaudeCodeOptions` | Claude Agent SDK, `ClaudeAgentOptions` (renamed in version 0.1.0) |
| Thinking capped with `max_thinking_tokens` | `effort` and `thinking` (adaptive); `max_thinking_tokens` is deprecated. On 5.x models do not use `{"type": "enabled", "budget_tokens": ...}` (module 07) |
| The tool that hands work to a subagent was called `Task` | It is called `Agent`; `Task` is still accepted, and the tool list in init still says `Task` |
| Thinking summaries shown by default | Since Opus 4.7, `display` defaults to `"omitted"`: to read `ThinkingBlock`, set `"summarized"` |
| Token counts on older models | Models since 4.7 use a new tokenizer, and the same text gives about 30% more tokens (module 06): measure agent costs again on the new models |

## Exercises

| Exercise | Task | Graded on |
|---|---|---|
| [`bai1_doc_ket_qua.py`](exercises/bai1_doc_ket_qua.py) | Summarize one run from its message stream: tools called, failed tools, number of turns, cost, success or not | a successful run, a run that hits `max_turns`, `success` with `is_error` |
| [`bai2_quyen.py`](exercises/bai2_quyen.py) | `can_use_tool` with `updated_input`, a `PreToolUse` hook that blocks by content | each allow/deny case, run together with the mock agent |
| [`bai3_tuy_chon.py`](exercises/bai3_tuy_chon.py) | A custom tool with an `enum` and a useful error; the options for an unattended agent (`dontAsk`) | the right temperature conversion, `is_error` on a wrong unit, every options field right |

```bash
CHAM="$PWD/en/modules/09-agent-sdk/exercises" CLAUDE_MOCK=1 uv run pytest modules/09-agent-sdk -q   # grade your work
CLAUDE_MOCK=1 uv run pytest modules/09-agent-sdk -q                                                  # grade the solutions
```

Review questions: [quiz.md](quiz.md).

## Next

Module 10 (MCP) goes deeper into MCP servers: you already used a server that runs inside your process in section 4. The sources of this module: [references.md](references.md).
