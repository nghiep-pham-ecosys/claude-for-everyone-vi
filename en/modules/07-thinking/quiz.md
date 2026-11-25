# Quiz · Module 07

Pick one answer. The answer and the explanation are in the folded part under each question.

**1.** On Haiku 5.5, the response has a `thinking` block with an empty `thinking` field. What does that mean?

- A. Claude did not think, and no thinking tokens were used
- B. Claude did think; the text is hidden because `display` defaults to `"omitted"`, and the tokens are still billed
- C. An API error

<details><summary>Answer</summary>

**B.** The thinking is encrypted in the `signature`. To read a summary, set `display: "summarized"`.
</details>

**2.** You change `display` from `"omitted"` to `"summarized"`. How does the cost change?

- A. It goes up with the length of the summary
- B. It does not change: you pay for all of the original thinking, whatever you see
- C. It goes down

<details><summary>Answer</summary>

**B.** `"omitted"` only makes the text of the answer arrive sooner when you stream.
</details>

**3.** You want Sonnet 5.5 to think as little as possible. What do you send?

- A. `thinking: {"type": "disabled"}`
- B. `thinking: {"type": "between_tools"}`, at effort `high` or lower
- C. `thinking: {"type": "enabled", "budget_tokens": 0}`

<details><summary>Answer</summary>

**B.** Sonnet 5.5 returns 400 with `disabled`; `budget_tokens` was removed on every 5.x model.
</details>

**4.** How do you reduce thinking on Opus 5.5?

- A. `thinking: {"type": "disabled"}`
- B. Lower `output_config.effort`
- C. `temperature: 0`

<details><summary>Answer</summary>

**B.** Opus 5.5 cannot turn thinking off. `temperature` returns 400.
</details>

**5.** `stop_reason` is `"max_tokens"`, the text is empty, and `thinking_tokens` equals `output_tokens`. What should you do first?

- A. Lower the effort
- B. Raise `max_tokens`
- C. Send the same request again

<details><summary>Answer</summary>

**B.** Thinking used up the hard cap. You paid for the thinking and got no answer. Lowering the effort is the next step, if the cost is still high.
</details>

**6.** Code sends the assistant turn back in a tool loop with `[b for b in msg.content if b.type in ("thinking", "text", "tool_use")]`. What is the hidden bug?

- A. There is no bug
- B. It drops `redacted_thinking` blocks, and the tool loop returns 400
- C. The blocks are in the wrong order

<details><summary>Answer</summary>

**B.** Send `msg.content` back unchanged, with no filter.
</details>

**7.** An app adds the current date and time to the `system` parameter in every request of a conversation. On Haiku 5.5 with a new account, what happens on turn 2?

- A. Nothing goes wrong
- B. 400: the thinking block of turn 1 fails the prefix check because `system` changed
- C. Thinking is quietly turned off

<details><summary>Answer</summary>

**B.** Keep `system` fixed; put the changing information in the newest turn or in a `system` message mid-conversation.
</details>

**8.** Your code runs with no error on your key, even though it changes `system` midway. What can you conclude?

- A. The code is right
- B. Nothing yet: accounts created before 2026-08-31 do not get a 400 on some models, but people with new accounts will
- C. The prefix check was removed

<details><summary>Answer</summary>

**B.** Check with this repo's mock (it always behaves like a new account) or with `block_binding` (beta).
</details>

**9.** Where is a `{"role": "system", "content": "..."}` message valid mid-conversation?

- A. At the start of the `messages` list
- B. Right after an assistant turn with `tool_use`, before the `tool_result`
- C. Right after a user turn, before an assistant turn or at the end of the list

<details><summary>Answer</summary>

**C.** For the start of the list, use the `system` parameter; between `tool_use` and `tool_result` it returns 400.
</details>

**10.** You want to know why Claude chose an answer. Which way fits on Opus 5.5?

- A. Add "Write out all of your thinking step by step in the answer"
- B. Set `display: "summarized"` and read the thinking block
- C. Add a `suy_nghi` ("thinking") field to the JSON schema

<details><summary>Answer</summary>

**B.** A and C may be refused with `reasoning_extraction`. If your users need a reason, ask for a short explanation instead of the whole thinking.
</details>
