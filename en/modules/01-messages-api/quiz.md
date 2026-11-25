# Quiz · Module 01

Pick one answer. The answer and the explanation are in the folded part under each question.

**1.** You send the second turn of a conversation, and you put only the new question in `messages`. What happens?

- A. Claude remembers the earlier turn through the `id` of the old message
- B. Claude knows nothing about the earlier turn
- C. The API returns 400 because the history is missing

<details><summary>Answer</summary>

**B.** The Messages API is stateless: each request stands alone. No history means no context. But the request is still valid, so there is no error.
</details>

**2.** On Haiku 5.5, which code gets the text answer right?

- A. `msg.content[0].text`
- B. `msg.content`
- C. `text_of(msg)`, which joins every block with `type == "text"`

<details><summary>Answer</summary>

**C.** Thinking is on by default, so the first block is often `thinking`. `content` is a list of blocks, not a string.
</details>

**3.** A response has `stop_reason == "max_tokens"`. Which conclusion is right?

- A. The answer is complete, just long
- B. The answer was cut off at the `max_tokens` cap
- C. The request was refused

<details><summary>Answer</summary>

**B.** Raise `max_tokens` or ask for a shorter answer, and do not use that text as a complete answer.
</details>

**4.** Thinking is hidden (`display: "omitted"`, the `thinking` field is empty). Do you pay for thinking?

- A. No, because you get no text
- B. Yes, thinking tokens count in `output_tokens` and toward `max_tokens`
- C. Yes, but at the input price

<details><summary>Answer</summary>

**B.** Hidden only means the text is not returned; the model still thinks. `usage.output_tokens_details.thinking_tokens` shows the thinking part.
</details>

**5.** When you send an assistant turn back in the history, which way is safest?

- A. Send only `text_of(msg)` to keep it short
- B. Send `msg.content` unchanged, including the empty thinking block
- C. Drop the assistant turn and keep only the user turns

<details><summary>Answer</summary>

**B.** Keep the thinking blocks unchanged and keep the history append-only. Filtering or editing thinking blocks can cause a 400 error, especially in a tool loop.
</details>

**6.** You get a 529 `overloaded_error`. What should you do?

- A. Fix the request and send it again
- B. Wait, then retry with backoff; the SDK already retried 2 times
- C. Change the API key

<details><summary>Answer</summary>

**B.** 529 means the API is overloaded overall; it is not a fault in your request. The SDK retries with exponential backoff; tune it with `max_retries`.
</details>

**7.** Which error should you **not** retry automatically?

- A. 429 `rate_limit_error`
- B. 500 `api_error`
- C. 400 `invalid_request_error`

<details><summary>Answer</summary>

**C.** A bad request sent again unchanged is still bad. You must fix the request.
</details>

**8.** When streaming, what is `usage.output_tokens` in the `message_delta` event?

- A. The number of new tokens since the last event
- B. The running total up to that point
- C. Always 0; you must count yourself

<details><summary>Answer</summary>

**B.** The number in `message_delta` is a running total. Adding them up gives a wrong number.
</details>

**9.** Which one is **not** a main reason to use streaming?

- A. The user sees text sooner
- B. A long request is less likely to be cut by the network for staying silent too long
- C. Streaming is cheaper than a normal call

<details><summary>Answer</summary>

**C.** The token price is the same. Streaming improves the experience and makes long requests more robust.
</details>

**10.** An old tutorial uses `temperature=0` for steady answers. What happens on 5.x models?

- A. It runs normally
- B. The API returns 400; Python SDK 1.0 and later also dropped this parameter
- C. It is silently ignored

<details><summary>Answer</summary>

**B.** For steady output, write a clear prompt (module 02) and use structured outputs (module 05).
</details>
