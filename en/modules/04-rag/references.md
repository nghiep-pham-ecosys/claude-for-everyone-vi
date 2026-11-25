# Sources · Module 04

Checked on **2026-11-09**. The lesson is written in this repo's own words. The English text is a translation of the Vietnamese edition; the check dates did not change. The BM25 formula is common knowledge in information retrieval; the repo uses the idf form `ln(1 + (N − n + 0.5)/(n + 0.5))` (never negative), as many popular search libraries do.

| Topic | Source | Used for |
|---|---|---|
| The `search_result` block: required fields, text only, placed in a user turn or inside a `tool_result`; a `tool_result` with a `search_result` must hold only `search_result` blocks; citations all or none; `search_result_location` (`source`, `title`, `search_result_index`, block indexes, `cited_text` not counted as tokens); whole blocks are cited; return text instead of an error when nothing is found; a "JSON only" prompt loses citations | [Search results](https://platform.claude.com/docs/en/build-with-claude/search-results) | Section 6, scripts 04–05, exercise 3, `claude_vi.rules.search_result_errors`, `_search_payload` in the mock |
| A collection under about 200,000 tokens can be sent whole; BM25 is strong on codes and exact terms; embeddings + BM25 beat embeddings alone; contextual retrieval (50–100 tokens of context per chunk); top-20 failed retrieval rate 5.7% → 2.9% (context for both embeddings and BM25) → 1.9% (with rerank); top-20 beats top-5/10; rank fusion | [Introducing Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) (Anthropic, 2024) | "Why learn this", sections 2, 4, 5 |
| Anthropic has no embedding model of its own; it points to outside providers | [Embeddings](https://platform.claude.com/docs/en/build-with-claude/embeddings) | Section 7 |
| `tool_choice` any/tool returns 400 on Opus 5.5, Sonnet 5.5, Fable 5.1, Fable 5.2 | [Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools), [Fable 5.2 migration guide](https://platform.claude.com/docs/en/models/fable-5-2/migration-guide) | Section 6, script 05 |
| Unicode NFC/NFD normalization, the `Mn` category | [Python `unicodedata`](https://docs.python.org/3/library/unicodedata.html) | Section 2, exercise 1 |

The numbers in the blog post were measured in 2024 on Anthropic's data, with Claude 3 Haiku generating the context. The lesson cites them only to show the direction of improvement; it does not claim similar results on other collections.

## Estimated cost

Scripts 01–02 make no API call. Script 03: 4 calls, `max_tokens` 256, each sending one short document (under 1,000 tokens). Script 04: 1 call. Script 05: 2–4 calls. Worst-case output with Haiku 5.5: (4 × 256 + 5 × 1,024) × $0.50/MTok ≈ $0.003; input under 20,000 tokens ≈ $0.002. The whole module costs under $0.01. This is an estimate, not yet measured with the real API.
