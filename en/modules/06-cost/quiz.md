# Quiz · Module 06

Pick one answer. The answer and the explanation are in the folded part under each question.

**1.** `usage` has `output_tokens: 300` and `output_tokens_details.thinking_tokens: 200`. How many output tokens do you pay for?

- A. 500
- B. 300
- C. 100

<details><summary>Answer</summary>

**B.** Thinking is already inside `output_tokens`. Adding 200 more counts it twice.
</details>

**2.** A request with the cache returns `input_tokens: 40`, `cache_read_input_tokens: 2000`, `cache_creation_input_tokens: 0`. How many tokens long is the prompt?

- A. 40
- B. 2,000
- C. 2,040

<details><summary>Answer</summary>

**C.** Total input = cache read + cache write + `input_tokens`. `input_tokens` is only the part after the last breakpoint.
</details>

**3.** You put `cache_control` on the block that holds the current time, at the end of the system prompt. What happens?

- A. The cache works as usual
- B. Every call writes the whole prefix to the cache and can never read it, so it costs more than no cache
- C. The API returns 400

<details><summary>Answer</summary>

**B.** The block changes every time, so the prefix is different every time. Put the breakpoint at the end of the part that **does not change**, before the time block.
</details>

**4.** Your system prompt is 300 tokens, has `cache_control`, and runs on Haiku 5.5. After the first call, `cache_creation_input_tokens` is 0. Why?

- A. A config error; the API will return 400 next time
- B. The prompt is shorter than the 512-token threshold, so it is not cached; the API reports no error
- C. Caching only exists on Opus

<details><summary>Answer</summary>

**B.** Under the threshold, nothing is cached and nothing is reported. Check `usage` after the first call.
</details>

**5.** With the 1-hour cache (write at 2x the input price), how many reads do you need at least to pay less than with no cache?

- A. 1
- B. 2
- C. 10

<details><summary>Answer</summary>

**B.** A 2x write + 1 read still costs more than 2 normal sends. From the second read on, it is cheaper. The 5-minute cache (1.25x) breaks even after 1 read.
</details>

**6.** How is `count_tokens` different from `create`?

- A. It takes no `max_tokens`, creates no message, uses no cache, and is free but has its own request limit
- B. It is billed like input tokens
- C. It also returns the expected number of output tokens

<details><summary>Answer</summary>

**A.** The count is an estimate of the input. You work out the output cap yourself from `max_tokens`.
</details>

**7.** You count a prompt with an old model and get 10,000 tokens, then use that number to estimate the cost on Opus 5.5. What is wrong?

- A. Nothing; tokens are the same everywhere
- B. Models from 4.7 on use a new tokenizer that gives about 30% more tokens (up to about 35% with Opus 5.5); you must count again with the right model
- C. Opus 5.5 does not support token counting

<details><summary>Answer</summary>

**B.** `count_tokens` counts with the tokenizer of the model you pass in.
</details>

**8.** You send a batch of 3 requests, `a`, `b`, `c`. The results come back in the order `c`, `a`, `b`. What do you do?

- A. Report a bug to the API
- B. Match them by `custom_id`; the order of the results is not guaranteed
- C. Send the batch again

<details><summary>Answer</summary>

**B.** Each request needs its own `custom_id` (1–64 characters: letters, digits, `-`, `_`).
</details>

**9.** One request in a batch has bad `params`. When do you find out, and do you pay for it?

- A. As soon as the batch is created; yes, you pay
- B. When the whole batch is done, that request is `errored`; you do not pay for it
- C. You never find out

<details><summary>Answer</summary>

**B.** `params` are checked asynchronously. That is why you should check each request before sending (`client.batch_create` does this). Only `succeeded` is billed.
</details>

**10.** Does turning on message threads for a 20-turn conversation lower the bill?

- A. Yes, you pay only for the new message
- B. Not by itself: a thread makes requests smaller, but the price does not change; to pay less, send a top-level `cache_control` in every request of the thread
- C. Yes, a thread cuts 50% like a batch

<details><summary>Answer</summary>

**B.** The docs: a thread does not change the price and does not turn on the cache by itself. A thread also expires after 5 minutes without use, or the API cannot continue it for another reason: when a continue gets 404 `thread_not_found`, resend the whole conversation.
</details>
