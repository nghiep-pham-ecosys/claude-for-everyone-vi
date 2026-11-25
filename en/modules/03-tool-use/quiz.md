# Quiz · Module 03

**1.** Claude returns a `tool_use` block for a tool you defined yourself. Who runs the function?

- A. Claude, on Anthropic's servers
- B. Your code
- C. The SDK runs it with no code from you

<details><summary>Answer</summary>

**B.** Claude only returns the request (`name`, `input`). The SDK tool runner can automate the loop, but the function is still your code.
</details>

**2.** According to the docs, which factor matters most for tool use quality?

- A. A short tool name
- B. A very detailed tool description
- C. Having `input_examples`

<details><summary>Answer</summary>

**B.** Write at least 3–4 sentences: what the tool does, when to use it, what the parameters mean, and what its limits are.
</details>

**3.** Which tool name is valid?

- A. `tra cứu AQI`
- B. `env_get_aqi`
- C. `get.aqi`

<details><summary>Answer</summary>

**B.** The name must match `^[a-zA-Z0-9_-]{1,128}$`.
</details>

**4.** Claude returns 2 `tool_use` blocks in one response. How do you send the results?

- A. Two user turns, one `tool_result` each
- B. One user turn with both `tool_result` blocks
- C. Only the result of the first tool

<details><summary>Answer</summary>

**B.** Each `tool_use` needs a `tool_result`, all in the very next user turn.
</details>

**5.** Which user turn causes a 400 error?

- A. `[tool_result, text]`
- B. `[text, tool_result]`

<details><summary>Answer</summary>

**B.** The `tool_result` blocks must come first.
</details>

**6.** You filter `msg.content` down to `text` and `tool_use` before sending it back in the tool loop. What happens on 5.x models?

- A. It works and saves tokens
- B. A 400 error, because the thinking block of the latest assistant turn was changed or dropped

<details><summary>Answer</summary>

**B.** Send `msg.content` back unchanged.
</details>

**7.** On `claude-sonnet-5-5`, you want the tool `input` to always have the right types. What do you do?

- A. `tool_choice={"type": "any"}`
- B. `"strict": true` on the tool definition
- C. Add "FILL IN THE RIGHT TYPES" to the prompt

<details><summary>Answer</summary>

**B.** A returns 400 on Sonnet 5.5. C guarantees nothing.
</details>

**8.** Your tool raises `ConnectionError`. What is the best way to handle it?

- A. Let the exception stop the program
- B. Send an empty `tool_result`
- C. Send a `tool_result` with `"is_error": true`, a description of the error, and a hint for the next step

<details><summary>Answer</summary>

**C.** Claude uses that information to try another way or to tell the user.
</details>

**9.** The tool result is the content of a web page. Where should you put it?

- A. In `system`, so Claude takes it seriously
- B. In the `tool_result`
- C. In a user text block

<details><summary>Answer</summary>

**B.** Outside content is untrusted data and can hold harmful instructions. Keep it in the `tool_result`.
</details>

**10.** Why does a tool loop need a turn limit?

- A. The API allows only 3 turns
- B. So the agent does not loop forever and burn money when something goes wrong
- C. It does not need a limit

<details><summary>Answer</summary>

**B.**
</details>
