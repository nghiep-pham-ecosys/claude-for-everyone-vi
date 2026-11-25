# Quiz · Module 02

**1.** According to the docs, what should you have **before** you start changing a prompt?

- A. A stronger model
- B. Success criteria, a way to measure against them, and a first draft of the prompt
- C. At least 10 examples

<details><summary>Answer</summary>

**B.** If you cannot measure, you cannot tell whether a change is better.
</details>

**2.** Which wording works better?

- A. "NEVER use ellipses."
- B. "The text will be read aloud by a speech engine, and it cannot read ellipses, so do not use them."

<details><summary>Answer</summary>

**B.** With a reason, Claude generalizes to similar cases on its own.
</details>

**3.** A prompt has a 50,000-token document and one question. How do you order them?

- A. The question first, the document after
- B. The document first, the question at the end
- C. The order does not matter

<details><summary>Answer</summary>

**B.** According to the docs, a question at the end can improve quality by up to 30% with multi-document input.
</details>

**4.** How many few-shot examples do the docs advise?

- A. 1
- B. 3–5
- C. The more the better, at least 20

<details><summary>Answer</summary>

**B.** Examples must be realistic, varied, and wrapped in `<example>`.
</details>

**5.** All 4 of your examples have the output `"tich_cuc"` ("positive"). What is the risk?

- A. There is no risk
- B. Claude learns the wrong pattern, "always answer tich_cuc"
- C. The API returns 400

<details><summary>Answer</summary>

**B.** Examples must be varied and cover the edge cases too.
</details>

**6.** On Haiku 5.5, which way forces the output to be JSON that matches a schema?

- A. Prefill the assistant turn with `"{"`
- B. `temperature=0` and "return only JSON"
- C. `output_config.format` with `type: "json_schema"`

<details><summary>Answer</summary>

**C.** A and B both return 400 on 5.x models.
</details>

**7.** Which schema will structured outputs reject?

- A. `{"type": "object", "properties": {"n": {"type": "integer"}}, "required": ["n"], "additionalProperties": false}`
- B. `{"type": "object", "properties": {"n": {"type": "integer", "minimum": 1}}, "required": ["n"], "additionalProperties": false}`

<details><summary>Answer</summary>

**B.** `minimum` is not supported. Check the value range in code after you get the result.
</details>

**8.** A structured output response has `stop_reason == "max_tokens"`. What should you do?

- A. `json.loads` it as usual
- B. Treat it as unusable: the JSON may be cut off; raise `max_tokens` and call again

<details><summary>Answer</summary>

**B.**
</details>

**9.** What is the default effort level of `claude-haiku-5-5`?

- A. `low`
- B. `medium`
- C. `high`

<details><summary>Answer</summary>

**B.** Haiku 5.5 and Opus 5.5 default to `medium`; Sonnet 5.5 and Fable 5.1 default to `high`.
</details>

**10.** Which statement about effort is **false**?

- A. Effort affects the text, the tool calls and the thinking
- B. Effort is a hard token budget that is never exceeded
- C. `"adaptive"` is a thinking mode, not an effort level

<details><summary>Answer</summary>

**B.** Effort is a behavior signal. The hard cap is `max_tokens`.
</details>
