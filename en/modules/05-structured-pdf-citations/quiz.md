# Quiz · Module 05

Pick one answer. The answer and the explanation are in the folded part under each question.

**1.** You send `transform_schema(PhepDo)` with `gia_tri: float = Field(ge=0)` ("gia tri" = value). What does the API guarantee about `gia_tri`?

- A. `gia_tri` is a number and is not negative
- B. `gia_tri` is a number; the "not negative" constraint is only in the description, so you must check it yourself
- C. Nothing at all

<details><summary>Answer</summary>

**B.** `transform_schema` drops `minimum` from the schema because the API does not support it, and copies it into the description. Read the result with `PhepDo.model_validate_json` to check it again.
</details>

**2.** A request has an `output_config.format` with 10 optional fields, and 3 tools with `strict: true`, each with 5 optional fields. What happens?

- A. It runs fine, because each schema is under 24
- B. Error 400, because the total of 25 optional fields goes over the limit of 24, counted across the request
- C. The API turns off strict on the third tool by itself

<details><summary>Answer</summary>

**B.** The limit is counted across every strict schema in the request. How to fix it: move some fields into `required`, drop strict on the tools that do not need it, or split the request.
</details>

**3.** What happens if you turn on citations and set `output_config.format` in the same request?

- A. The JSON gets an extra citations field
- B. Error 400
- C. Citations are silently ignored

<details><summary>Answer</summary>

**B.** Citations must insert cited blocks into the text, which does not fit with JSON forced by a schema. Split it into two turns, or ask for one line per field, with citations.
</details>

**4.** A sentence sits fully on page 3 of a PDF. Which values does its citation have?

- A. `start_page_number=2, end_page_number=3`
- B. `start_page_number=3, end_page_number=3`
- C. `start_page_number=3, end_page_number=4`

<details><summary>Answer</summary>

**C.** Pages count from 1, and the end is excluded.
</details>

**5.** You have a meter log, one event per line, and you want Claude to cite each whole line. Which document type do you use?

- A. Plain text, with the lines joined by `\n`
- B. Custom content, one text block per line
- C. PDF

<details><summary>Answer</summary>

**B.** Custom content is not cut further: each block is one citation unit. Plain text is cut into sentences, and lines with no period can be merged or cut in odd places.
</details>

**6.** You put the experiment code in the `context` field of a document. Can Claude cite that code?

- A. Yes
- B. No: `title` and `context` are sent to Claude but are never cited

<details><summary>Answer</summary>

**B.** The content you want cited must be in `source`.
</details>

**7.** Citations are on, and the prompt says "Return only one JSON object, nothing else". What can the result be?

- A. Error 400
- B. The request succeeds, but with very few or no citations
- C. JSON with full citations

<details><summary>Answer</summary>

**B.** The docs warn about exactly this case. Ask for one line per field as `name: value`, and a source for each line.
</details>

**8.** When you split the line `gio_lay: 08:20` ("gio lay" = sampling time), what should you do?

- A. Split at every colon
- B. Split at the first colon
- C. Drop the line because it has several colons

<details><summary>Answer</summary>

**B.** A field name has no colon, but a value can have one.
</details>

**9.** A PDF has 2 pages. How do you estimate the input tokens?

- A. Count only the characters of the text
- B. About 1,500–3,000 text tokens per page, plus the image tokens of each page
- C. A fixed 1,000 tokens per page

<details><summary>Answer</summary>

**B.** The API turns each page into an image and sends the extracted text along. For an exact number, use token counting.
</details>

**10.** The check step finds that the quote really exists on page 1 and holds the number 276. What does that prove?

- A. 276 is surely the yield strength of specimen A1
- B. 276 appears in a real sentence on page 1; it does not yet prove that it is tied to the right quantity
- C. Nothing

<details><summary>Answer</summary>

**B.** A citation proves the source, not the reading. To be stricter, also check the name of the quantity, or have a person review.
</details>
