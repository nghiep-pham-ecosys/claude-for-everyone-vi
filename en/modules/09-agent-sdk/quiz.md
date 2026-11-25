# Quiz · Module 09

**1.** What is the main difference between the Agent SDK and the Client SDK (`anthropic`)?

- A. The Agent SDK is cheaper
- B. The Agent SDK runs the tool loop and has built-in tools; with the Client SDK you write the loop yourself
- C. The Agent SDK needs no API key

<details><summary>Answer</summary>

**B.** The Agent SDK runs the Claude Code CLI as a child process, and it runs the loop, runs the tools and manages the context for you. You still need an API key.
</details>

**2.** You set `allowed_tools=["mcp__ptn__tra_lich"]`. Can Claude call `Bash`?

- A. Never: only the tools in `allowed_tools` exist
- B. Maybe: `allowed_tools` only pre-approves; `Bash` still exists and goes on to `permission_mode` and `can_use_tool`
- C. Yes, it always runs without approval

<details><summary>Answer</summary>

**B.** To remove built-in tools fully: `tools=[]`, or the bare name in `disallowed_tools`.
</details>

**3.** You have `allowed_tools=["mcp__ptn__*"]` and a `can_use_tool` that logs every call. The log is empty. Why?

- A. A bug in the SDK
- B. A call already approved by an allow rule does not reach `can_use_tool`; to see every call, use a `PreToolUse` hook
- C. `can_use_tool` runs only for built-in tools

<details><summary>Answer</summary>

**B.** `can_use_tool` is the last step of the permission flow.
</details>

**4.** The server is made with `create_sdk_mcp_server(name="phong-thi-nghiem", tools=[tra_lich])` and registered as `mcp_servers={"ptn": server}`. What is the full name of the tool?

- A. `mcp__phong-thi-nghiem__tra_lich`
- B. `mcp__ptn__tra_lich`
- C. `tra_lich`

<details><summary>Answer</summary>

**B.** The middle part is the key in `mcp_servers`, not the `name`.
</details>

**5.** A `PreToolUse` hook has `matcher="ghi_nhat_ky.*xoá"` to block delete commands ("xoá" is Vietnamese for "delete"). Does it block them?

- A. Yes
- B. No: `matcher` is compared only with the tool name; filtering by arguments must happen in the callback
- C. Yes, but only in `bypassPermissions`

<details><summary>Answer</summary>

**B.** Set `matcher` by name (for example `"^mcp__ptn__"`), then check `input_data["tool_input"]` in the callback.
</details>

**6.** `disallowed_tools=["Bash"]` together with `permission_mode="bypassPermissions"`. Does `Bash` run?

- A. Yes, bypass wins over everything
- B. No: deny rules win over `bypassPermissions`, and even over a hook that has allowed the call
- C. It depends on `can_use_tool`

<details><summary>Answer</summary>

**B.** Deny rules come right after hooks in the permission flow, and no mode can get past them.
</details>

**7.** You do not set `max_turns` or `max_budget_usd`. How many turns can the agent run at most?

- A. 10 turns
- B. No limit
- C. Until `max_tokens` runs out

<details><summary>Answer</summary>

**B.** By default there is no cap. Set both for every agent that runs unattended.
</details>

**8.** The first run of a session costs $0.010. You `resume` that session, and `ResultMessage` reports `total_cost_usd=0.014`. How much did both runs cost?

- A. $0.024
- B. $0.014
- C. $0.004

<details><summary>Answer</summary>

**B.** The result of a resumed session already includes the cost of the earlier runs. And it is still a client-side estimate, not a bill.
</details>

**9.** You did not set `setting_sources`, and your agent follows a strange instruction. What could be the cause?

- A. By default the SDK loads every settings source, including the project's `CLAUDE.md` and the one in `~/.claude`
- B. The default system prompt is the one of Claude Code
- C. This cannot happen

<details><summary>Answer</summary>

**A.** Set `setting_sources=[]` to drop the user/project/local settings and `CLAUDE.md`. It does not isolate fully: the administrator's policy, `~/.claude.json` and auto memory are still loaded. The default system prompt is a minimal one, not the one of Claude Code.
</details>

**10.** `query()` raises `ResultError` with `subtype="error_max_turns"`. Can you still read `ResultMessage`?

- A. No, the error is raised first
- B. Yes: the SDK returns `ResultMessage` first and then raises the error; catch the error around the `async for` loop
- C. Only with `ClaudeSDKClient`

<details><summary>Answer</summary>

**B.** Script 03 and `doc_het()` do exactly this. `ResultError` also has `subtype` and `session_id`, and it is raised for every error result, including `success` with `is_error=True`.
</details>
