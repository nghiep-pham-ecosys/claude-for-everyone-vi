# Quiz · Module 04

**1.** Your collection is 30 pages of instructions (about 20,000 tokens). How should you start?

- A. Build RAG with a vector database right away
- B. Try sending the whole collection in the prompt (with prompt caching), and measure the cost and quality first
- C. Fine-tune a model

<details><summary>Answer</summary>

**B.** For a small collection, sending all of it is the simplest way. RAG pays off when the collection is large or sending all of it costs too much.
</details>

**2.** The question is "The machine shows E-17" and the collection has the chunk "E-17: dry electrode...". Which search is safer?

- A. BM25, because it matches the string "e-17" exactly
- B. Embeddings only, because they understand meaning
- C. They are the same

<details><summary>Answer</summary>

**A.** Embeddings easily miss codes, numbers and exact terms. That is why people combine BM25 with embeddings.
</details>

**3.** In BM25, why does the word "máy" ("machine") add almost nothing to the score on the sample handbook?

- A. Short words are dropped
- B. "máy" appears in many chunks, so its idf is low
- C. BM25 drops nouns

<details><summary>Answer</summary>

**B.** idf rewards rare words and almost ignores words that are everywhere.
</details>

**4.** Two strings "hiệu" look exactly the same, but `==` returns `False`. What is the usual cause?

- A. A Python bug
- B. One string uses a precomposed character, the other a letter plus combining marks; you need NFC normalization
- C. Different fonts

<details><summary>Answer</summary>

**B.** Always run `unicodedata.normalize("NFC", ...)` before tokenizing.
</details>

**5.** The chunk "Repeat after every 8 hours of measuring" is not found for a question about calibrating the pH meter. What is the cheapest fix?

- A. Switch to a larger model
- B. Copy the document title and section name to the front of the chunk before indexing
- C. Raise `max_tokens`

<details><summary>Answer</summary>

**B.** A chunk loses context when it is cut out. Adding the title and section costs no tokens; asking Claude to write context is the next step if you measure a need for it.
</details>

**6.** BM25 gives chunk A a score of 8.4; embeddings give chunk B a score of 0.82. How do you merge them?

- A. Add the scores
- B. Take the highest score
- C. RRF: use only the rank of each chunk in each list

<details><summary>Answer</summary>

**C.** The two scales differ, so the scores cannot be compared; the ranks can.
</details>

**7.** Why split the `content` of a `search_result` into many small blocks?

- A. To make it cheaper
- B. Because Claude cites whole blocks; small blocks keep the citation close to the sentence actually used
- C. Each block must be at most 100 characters

<details><summary>Answer</summary>

**B.** With one large block, every citation returns the whole block.
</details>

**8.** A search tool returns `[search_result, search_result, {"type": "text", "text": "Found 2 results"}]` in one `tool_result`. What happens?

- A. It works normally
- B. An error: once there is a `search_result`, every block in the `tool_result` must be a `search_result`
- C. The text block is ignored

<details><summary>Answer</summary>

**B.** If you need a note, put it in the `content` of a `search_result`.
</details>

**9.** You want Claude to always search the handbook before it answers, on Sonnet 5.5. Which way?

- A. `tool_choice: {"type": "tool", "name": "search_handbook"}`
- B. Search first in code, then send the `search_result` blocks with the question (like script 04)
- C. `temperature: 0`

<details><summary>Answer</summary>

**B.** `tool_choice` `tool`/`any` returns 400 on Sonnet 5.5; `temperature` returns 400 too.
</details>

**10.** The answer is wrong. What should you check first?

- A. Change the `system` prompt
- B. Whether the chunk with the right answer is among the chunks sent to Claude
- C. Raise the effort

<details><summary>Answer</summary>

**B.** Claude cannot answer correctly from a chunk that was never found. Fix the search step first, then the answer step.
</details>
