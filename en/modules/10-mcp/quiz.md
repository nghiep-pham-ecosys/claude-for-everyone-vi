# Quiz · Module 10

**1.** In MCP, who asks the user for consent before a tool is called?

- A. The server
- B. The host (the application with the LLM)
- C. Nobody, the tool just runs

<details><summary>Answer</summary>

**B.** The host manages the clients, keeps the safety rules and asks the user for consent. By design, a server should not see the whole conversation.
</details>

**2.** Your stdio server has a `print("debug")` line. What happens?

- A. Nothing, the client ignores it
- B. It can break the connection: stdout is only for MCP messages; logs must go to stderr
- C. The line is shown to the user

<details><summary>Answer</summary>

**B.** Every line on stdout must be a JSON-RPC message.
</details>

**3.** Who controls each server-side primitive?

- A. Tool: the user; resource: the model; prompt: the application
- B. Tool: the model; resource: the application; prompt: the user
- C. The model controls all three

<details><summary>Answer</summary>

**B.** Claude picks when to call a tool; the host decides which resource goes into the context; the user picks a prompt like a shortcut command.
</details>

**4.** A server declares a tool `clean_up` with `read_only_hint=True`. Should the host run it without asking?

- A. Yes, the server said it is read-only
- B. No: annotations are only hints, not to be trusted if the server is not trusted; the host keeps its own list of tools that run without asking
- C. Only if `idempotent_hint=True`

<details><summary>Answer</summary>

**B.** The rule of this module: with a server you do not trust yet, annotations may only make the host more careful (for example, `destructive_hint=True` means always ask). The spec allows you to trust annotations when the server is trusted.
</details>

**5.** In a tool of `MCPServer` (SDK 2.x), you `raise ValueError("missing sample ID")`. What does the model see?

- A. `missing sample ID`
- B. Only `Error executing tool <name>`; the real message stays in the server log. For the model to read it, `raise ToolError(...)`
- C. Nothing, the connection drops

<details><summary>Answer</summary>

**B.** `ToolError` is an expected error: the client gets `is_error=True` with the message. Any other exception (except `MCPError`) is treated as a crash. Script 02 shows both.
</details>

**6.** What is the big difference between MCP spec 2026-07-28 and 2025-11-25?

- A. JSON-RPC was dropped
- B. The `initialize` handshake was dropped: each request carries its own protocol version and client capabilities
- C. Only the stdio transport is left

<details><summary>Answer</summary>

**B.** The server must not rely on an earlier request. Sessions in Streamable HTTP were dropped too.
</details>

**7.** Sample code online says `from mcp.server.fastmcp import FastMCP`. Does it run with `mcp` 2.3.0?

- A. Yes
- B. No: SDK 2.x renamed `FastMCP` to `MCPServer` (`mcp.server.mcpserver`) and moved attributes to `snake_case`
- C. Only on Python 3.10

<details><summary>Answer</summary>

**B.** The old import raises `ModuleNotFoundError` with a link to the migration guide.
</details>

**8.** You want Claude (through the Messages API) to use an MCP server that runs over stdio on your laptop. Can the MCP connector do it?

- A. Yes, just declare `command`
- B. No: the connector only reaches remote servers over HTTPS; for a stdio server, the host builds the bridge itself (script 03) or you use the Agent SDK / Claude Code
- C. Yes, but only for resources

<details><summary>Answer</summary>

**B.** The connector also supports only tools, not resources or prompts.
</details>

**9.** When you turn a `CallToolResult` into a `tool_result`, you forget to copy `is_error`. What happens?

- A. Nothing
- B. Claude thinks the tool succeeded and may answer based on an error message
- C. The API returns 400

<details><summary>Answer</summary>

**B.** Keep `is_error` so Claude knows it must fix the parameters or try another way.
</details>

**10.** An MCP tool is named `schedule.check` (valid in the MCP spec). Can you send that name as is in the `tools` of the Messages API?

- A. Yes
- B. No: Messages API tool names accept only letters, digits, `_` and `-`; the host must rename it and keep a reverse lookup map
- C. Yes, if you add the prefix `mcp__`

<details><summary>Answer</summary>

**B.** Exercise 2 does exactly this: add the server prefix, replace invalid characters, cut to 128 characters.
</details>
