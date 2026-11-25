# 10 · MCP (Model Context Protocol)

**Type:** Learn + Build · **Time:** about 2 hours · **Needs:** modules 03, 08 and 09 · **Cost:** $0. The MCP server and client run on your machine and make no API call. Only script 03 calls Claude: $0 in mock mode, under $0.01 if you run it for real with `claude-haiku-5-5` (see [references.md](references.md))

## Goals

After this module you can:

- Say what MCP is and who does what: host, client, server.
- Tell apart the three things a server offers: tools, resources, prompts, and who controls each one.
- Write a small MCP server with the official Python SDK (`mcp` 2.x) and run it over stdio.
- Write a client that calls tools, reads resources, gets prompts, and reads the results right (`content`, `structured_content`, `is_error`).
- Bridge MCP tools to Claude as the host, and keep your own approval rules instead of trusting the server's annotations.
- Name three other ways to use MCP with Claude: the MCP connector of the Messages API, the Agent SDK, Claude Code.

| Learn | Build |
|---|---|
| Read sections 1–8 and run the 3 scripts in `python/` | Do the 3 exercises in `exercises/`, graded by tests |

## Why learn this

In modules 03, 08 and 09, the tools live right in your code. To reuse the same set of tools in many applications (Claude Code, Claude Desktop, your agent, other people's apps), you must rewrite the glue for each one. **MCP** is an open protocol that standardizes that glue: write a server once, and every host that speaks MCP can use it.

The price: the tools come from **someone else**. A tool description is text that the model reads, so an unknown server can steer the model. This module teaches both how to use MCP and how to stay in control.

## The minimum that runs

```bash
uv run python en/modules/10-mcp/python/01_kham_pha_may_chu.py
```

| File | Main idea |
|---|---|
| [`may_chu_ptn.py`](python/may_chu_ptn.py) | The MCP server: tools `check_schedule`, `view_sample` (read-only), `write_log` (has a side effect), the resource `lab://handbook`, the prompt `ask_schedule` |
| [`01_kham_pha_may_chu.py`](python/01_kham_pha_may_chu.py) | The client starts the server over stdio, and shows the protocol version, the tools, resources and prompts |
| [`02_goi_tool.py`](python/02_goi_tool.py) | Call tools, read structured results, the kinds of errors, read a resource, get a prompt |
| [`03_claude_dung_mcp.py`](python/03_claude_dung_mcp.py) | The host bridges MCP tools to Claude (`ClaudeVi`, mock mode) and approves tools with side effects |
| [`cau_noi.py`](python/cau_noi.py) | Shared code ("cau noi" means bridge): stdio parameters, MCP tool to Messages API tool, result to `tool_result`, approval rules |

The server and the client here are **real**: the SDK `mcp` 2.3.0 is already a dependency of the repo, and everything runs on your machine, with no network and no API key. Only the Claude part of script 03 uses the mock (`CLAUDE_MOCK=1`). When you run script 02, the lines that start with `Tool ...` are the server log written to stderr: that is the stdio rule from section 1. The server's resource is the equipment handbook of module 06, which is in Vietnamese.

## 1. Host, client, server

| Role | What it is | In this module |
|---|---|---|
| **Host** | The application with the LLM: it manages clients, asks the user for consent, talks to the model | Script 03 |
| **Client** | One connection to **one** server, inside the host | `mcp.Client` |
| **Server** | A program that offers tools, resources and prompts | `may_chu_ptn.py` |

A host has many clients, and each client talks to exactly one server. By design, a server should not see the whole conversation or the other servers; the host keeps this boundary (for example: do not stuff the whole conversation into a tool parameter).

MCP has two layers:

- **The data layer:** JSON-RPC 2.0 messages, a standard JSON format for requests and responses; each request has an `id` to match it with its response, and a notification is a one-way message that needs no reply.
- **The transport layer:** **stdio** (the host runs the server as a child process, one message per line on stdin/stdout) or **Streamable HTTP** (a remote server, one POST request per message). The old HTTP+SSE transport is deprecated.

The stdio rule: the server may write **only** MCP messages to stdout; logs go to stderr. One stray `print()` in the server is enough to break the connection. That is why `may_chu_ptn.py` runs as a server only with the `--stdio` flag.

## 2. Protocol version: 2026-07-28

Why you need to know this: most sample code and articles online still follow version 2025-11-25, so you will meet old ideas. The current version of the spec is **2026-07-28** (a version name is the date of the last breaking change). Compared with 2025-11-25, a lot changed:

- **No more handshake** (the greeting at the start of a connection). Before, every connection started with `initialize`. Now each request carries its own protocol version and capabilities (the list of features the client supports) in `_meta`; the server must not rely on an earlier request. There is a new `server/discover` request to ask what the server supports (the client may skip it).
- **No more sessions** in Streamable HTTP. A tool that needs state takes an explicit "handle" in its parameters.
- The server no longer sends requests to the client on its own; instead there are **Multi Round-Trip Requests**: the server returns an `InputRequiredResult`, and the client sends the request again with the answer.
- **Deprecated:** sampling, roots and logging. On the client side, only elicitation (asking the user for input) is not deprecated.

The Python SDK's `mcp.Client` by default (`mode="auto"`) tries `server/discover` first; with an old server it falls back to `initialize`. Script 01 prints the agreed version: `2026-07-28`.

## 3. The three things a server offers

| Primitive | Who controls it | Example |
|---|---|---|
| **Tool** | The model: Claude picks when to call it | `check_schedule`, `write_log` |
| **Resource** | The application: the host decides what goes into the context | `lab://handbook` |
| **Prompt** | The user: picks it like a shortcut command | `ask_schedule` |

Tools are the part used most. Each tool has:

- `name`: the spec recommends (SHOULD) 1–128 characters from `A-Z a-z 0-9 _ - .`, unique within a server. Because it is only a recommendation, the host must still cope with names that break it. The Messages API does not accept `.` in a tool name (exercise 2).
- `description`: the model reads it to decide whether to call the tool. This is also where a bad server can inject instructions (section 6).
- `inputSchema`: the JSON Schema of the parameters.
- `outputSchema` (optional): when present, the result carries `structuredContent` that matches this schema, and should also carry the same JSON as text for older clients.
- `annotations`: `readOnlyHint` (default false), `destructiveHint` (default true, meaningful only when `readOnlyHint` is false), `idempotentHint` (default false), `openWorldHint` (default true). If the server does not set them, the Python attribute is `None`. **They are only hints**: the spec tells clients not to trust them if the server is not trusted.

## 4. Write a server with the Python SDK 2.x

```python
from typing import Literal, TypedDict
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

server = MCPServer("lab", version="1.0.0")

class DeviceSchedule(TypedDict):
    device_id: str
    schedule: str

@server.tool(annotations=ToolAnnotations(read_only_hint=True))
def check_schedule(device_id: Literal["HV-200", "LN-1200", "QS-3"]) -> DeviceSchedule:
    """Check the bookings of one piece of lab equipment."""
    return {"device_id": device_id, "schedule": SCHEDULE[device_id]}

server.run()   # stdio by default
```

- The tool name comes from the function name, the description from the docstring, and `inputSchema` from the type hints. `Literal` becomes `enum`. A parameter with no default value is required.
- The return type becomes `outputSchema`. A `TypedDict`, a Pydantic model, a dataclass or a `dict[str, ...]` gives an object `structured_content`. A `str`, `int`... is wrapped as `{"result": ...}`.
- Parameters that break the schema are stopped **before** the function runs.
- **Errors:** `raise ToolError("...")` for an expected error: the client gets `is_error=True` with the message (prefixed with `Error executing tool <name>:`). Any other exception (except `MCPError`, which becomes a JSON-RPC error) is treated as a crash: the model only sees `Error executing tool <name>`, and the real message stays in the server log. Script 02 shows both: `write_log` uses `ToolError`, and `view_sample` with an unknown ID crashes.
- Version 2 changed a lot from 1.x: `FastMCP` was renamed to `MCPServer` (`mcp.server.mcpserver`); the attributes of the data types are `snake_case` in Python (`input_schema`, `is_error`, `structured_content`), while the JSON on the wire is still `camelCase`. Code and articles for 1.x online do not run as is with 2.x.

## 5. Write a client

```python
from mcp import Client, StdioServerParameters

params = StdioServerParameters(command=sys.executable, args=["may_chu_ptn.py", "--stdio"])
async with Client(params) as mcp:
    print(mcp.protocol_version, mcp.server_info)
    tools = (await mcp.list_tools()).tools
    res = await mcp.call_tool("check_schedule", {"device_id": "HV-200"})
    print(res.is_error, res.structured_content, res.content)
```

- `Client(...)` takes a URL (Streamable HTTP), a `StdioServerParameters` (starts a child process), a transport you write, or the server object itself (connected in process, for tests: `Client(server)`). The module's exercises and tests use the last one.
- `Client` is an async context manager: entering it connects, leaving it closes. You cannot reuse it after you leave. The scripts set `read_timeout_seconds=30` so they do not hang forever if the server breaks.
- A stdio server does **not** inherit all your environment variables: the SDK passes only a few safe ones (`HOME`, `PATH`...) plus what you put in `StdioServerParameters(env={...})`. The host decides what the server sees. In Claude Code, the equivalent is `claude mcp add --env KEY=value`.
- The result of `call_tool`: `content` (blocks for the model to read), `structured_content` (data for code), `is_error`.
- **Two kinds of errors in the spec:** an error while running a tool comes back in the result with `isError: true`, so the model can read it and fix its call; a protocol error (a bad request, or an unknown tool according to the spec) is a JSON-RPC error. The Python SDK 2.3.0 returns even an unknown tool as `is_error=True`; `Client` raises `MCPError` only when the server returns a JSON-RPC error.

## 6. Bridge MCP to Claude: the host is the bridge

The Messages API does not talk to a server running on your machine by itself. The host is the bridge (script 03):

1. `list_tools` on the server, and turn each tool into a Messages API `{"name", "description", "input_schema"}`.
2. Send them to Claude; Claude returns `tool_use`.
3. **The host approves**, then calls `call_tool` on the server.
4. Turn the `CallToolResult` into a `tool_result` block (keep `is_error`) and send it back. Loop, like the agent loop of module 08.

The approval rules live in the **host**, not in the server:

- The spec (the Tools page): there SHOULD always be a human who can refuse a tool call, and the client SHOULD ask for confirmation before sensitive operations; the overview page states the principle that the host asks for consent before it calls a tool. `RUN_WITHOUT_ASKING` in `cau_noi.py` is consent the user gives **in advance** for a few read-only tools: it is set by the host or the user, never by the server. Every other tool is asked about at each call.
- `read_only_hint=True` is what **the server says about itself**. A bad server can label a tool that deletes data as "read-only". The host keeps its own list of tools that may run without asking. The rule of this module: with a server you do not trust yet, annotations may only make the host **more careful** (exercise 3). The spec allows you to trust annotations when the server is trusted.
- Tool results and tool descriptions are **untrusted data**, as in module 08, section 6. The MCP docs warn about "tool poisoning" (a tool description that holds instructions for the model) and about descriptions that change after you approved them.
- A server that runs over stdio is **not a sandbox**: it runs with your permissions. Install only servers you trust, and look at the exact command that will run before you install.

The `anthropic` SDK has helpers for this (`anthropic.lib.tools.mcp`, installed with the extra `anthropic[mcp]`; `async_mcp_tool` works with the tool runner). This module writes its own bridge so you can see each step and set your own approval rules.

## 7. Three other ways for Claude to use MCP

| Way | Server | Supports | Notes |
|---|---|---|---|
| **MCP connector** of the Messages API (beta) | Remote servers only, over HTTPS (Streamable HTTP or SSE); **no** stdio | Tools only (no resources, no prompts) | Declare `mcp_servers` (`type: "url"`, `url`, `name`, `authorization_token`) and a `{"type": "mcp_toolset", "mcp_server_name": ...}` in `tools`. Header `mcp-client-2026-09-15` (newer: everything in the 2025-11-20 version plus pinning the tool list; Claude API, Google Cloud) or `mcp-client-2025-11-20` (every platform, including Claude Platform on AWS and Microsoft Foundry). The response has `mcp_tool_use` and `mcp_tool_result` blocks; with the 2026-09-15 header there is also `mcp_tool_listing`, which you must send back unchanged. You handle OAuth yourself. Not covered by ZDR |
| **Agent SDK** (module 09) | stdio (`command`), HTTP/SSE (`url`), or in process (`create_sdk_mcp_server`) | Tools | Names are `mcp__<server>__<tool>`; you must grant permission explicitly, and the recommended way is `allowed_tools` (for example `mcp__<server>__*`) |
| **Claude Code** | `claude mcp add --transport http <name> <url>` or `claude mcp add <name> -- <command>` | Tools, resources (`@`), prompts (`/` commands) | Scopes: local, project (`.mcp.json`), user |

To block write tools in the MCP connector: set `default_config: {"enabled": false}`, then turn on each read-only tool in `configs`. There is no separate "allowlist" field.

## 8. Safety with other people's servers

- **Tool poisoning:** a tool description holds hidden instructions for the model. Read the descriptions before you turn a server on; watch for changes.
- **Prompt injection through data:** an honest server can still return content written by someone else (a web page, an e-mail). Keep it in `tool_result`; do not put it in `system`.
- **No token passthrough:** the spec forbids a server from passing the client's token as is to another API ("token passthrough").
- **Local servers:** they run with your permissions. An app that installs a server in one click must show the exact command and ask for consent.
- **HTTP servers running on your machine:** bind to `localhost`, check the `Origin` header, require authentication.

## Common traps

- **Printing to stdout in a stdio server.** It breaks the protocol; log to stderr.
- **Trusting the server's annotations** to skip approval. The host keeps its own list.
- **Copying SDK 1.x code** (`FastMCP`, `inputSchema` in Python) into SDK 2.x. `ClientSession` + `initialize()` still exist in 2.x as a low-level API, but `initialize()` forces the old handshake (2025-11-25); use `mcp.Client`.
- **Thinking a stdio server sees your environment variables.** Pass them with `env=`.
- **Raising a plain exception in a tool** and thinking the model can read the message. Use `ToolError`.
- **Dropping `is_error` when you build the `tool_result`.** Claude will think the tool succeeded.
- **Putting `.` in a tool name** and sending it straight to the Messages API (tool names there accept only `[a-zA-Z0-9_-]`).
- **Using the MCP connector for a server on your machine.** The connector can only reach remote servers over HTTPS.
- **Relying on sampling or roots** in a new design: they are deprecated since 2026-07-28.

## What changed with 5.x models

MCP is a protocol; it is not tied to a model. The changes that matter for this module:

| Before | Now |
|---|---|
| Every connection started with `initialize` (spec 2025-11-25) | Spec 2026-07-28: no handshake, each request carries its own version and capabilities |
| Python SDK 1.x: `FastMCP`; a transport context manager + `ClientSession` + calling `initialize()` by hand | SDK 2.x (since 2026-07-28): `MCPServer`; `mcp.Client`, one class for every transport |
| MCP connector: `tool_configuration` in `mcp_servers` (header `mcp-client-2025-04-04`) | `mcp_toolset` in `tools` (header `mcp-client-2025-11-20` or `mcp-client-2026-09-15`); the old header is deprecated |
| The host's tool loop | On 5.x models it still follows the rule of module 07: send back the assistant turn unchanged, thinking blocks included; script 03 does that |

## Exercises

| Exercise | Task | Graded on |
|---|---|---|
| [`bai1_may_chu.py`](exercises/bai1_may_chu.py) | A temperature conversion server: `Literal` becomes `enum`, `TypedDict` becomes `structured_content`, `ToolError`, annotations, one resource | calls through `Client(server)` in process |
| [`bai2_cau_noi.py`](exercises/bai2_cau_noi.py) | A host that bridges several servers: name prefix, replace invalid characters, cut to 128 characters, a reverse lookup map | names valid for the Messages API, clashes reported |
| [`bai3_duyet.py`](exercises/bai3_duyet.py) | Approval rules that do not trust annotations; `CallToolResult` to `tool_result` | a server that calls itself "read-only" still needs approval; `is_error` kept |

```bash
CHAM="$PWD/en/modules/10-mcp/exercises" CLAUDE_MOCK=1 uv run pytest modules/10-mcp -q   # grade your work
CLAUDE_MOCK=1 uv run pytest modules/10-mcp -q                                            # grade the solutions
```

The function names in the exercises stay in Vietnamese, because the same tests grade the Vietnamese and the English files; each file explains the names. Review questions: [quiz.md](quiz.md).

## Next

Modules 11–15 (Claude Code, Agent Skills, Evals, Production, Research) are open to community contributions. Sources for this module: [references.md](references.md).
