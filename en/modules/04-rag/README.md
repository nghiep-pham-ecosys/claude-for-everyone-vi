# 04 · RAG: find the documents, then answer with sources

**Type:** Learn + Build · **Time:** about 2.5 hours · **Needs:** modules 01–03, best after 05 · **Cost:** $0 in mock mode; under $0.01 if you run it for real with `claude-haiku-5-5` (prices checked 2026-10-24, see [references.md](references.md)). The search step runs fully on your machine: no API, no embedding model.

## Goals

After this module you can:

- Tell when you need RAG and when you can just put the whole document in the prompt.
- Write BM25 for Vietnamese from scratch, and see why it is good at finding error codes, device codes and numbers.
- Split documents into chunks without losing context.
- Merge two rankings with Reciprocal Rank Fusion (RRF).
- Give the chunks you found to Claude in `search_result` blocks, and read the `search_result_location` citations.
- Let Claude call a search tool on its own when it needs to.

| Learn | Build |
|---|---|
| Read sections 1–7 and run the 5 scripts in `python/` | Do the 3 exercises in `exercises/`, graded by tests |

## Why learn this

Claude knows nothing about your internal documents: a lab handbook, a machine manual, company rules. For Claude to answer from those documents, you must put them in the prompt.

When the collection is small, the simplest way is to send all of it. Anthropic's Contextual Retrieval blog post (2024) suggests: if the collection is under about 200,000 tokens, just send all of it, together with prompt caching to keep it cheap. Models today have much larger context windows, but every request still pays for every token you send, and the longer the documents, the harder it is for Claude to focus on the right part.

RAG (Retrieval-Augmented Generation) works differently: it first **finds** the few most relevant chunks, and sends only those. The quality of the answer depends mostly on the search step. Claude cannot answer correctly from a chunk that was never found.

## The minimum that runs

```bash
CLAUDE_MOCK=1 uv run python en/modules/04-rag/python/01_bm25.py
```

| Script | Main idea | Calls Claude? |
|---|---|---|
| [`01_bm25.py`](python/01_bm25.py) | BM25 on the handbook; error codes; a question typed without accents | No |
| [`02_ngu_canh.py`](python/02_ngu_canh.py) | Add the title and section to the front of each chunk: the right chunk climbs from rank 14 to 4 | No |
| [`03_ngu_canh_claude.py`](python/03_ngu_canh_claude.py) | Ask Claude to write a context sentence for each chunk | Yes, 4 calls |
| [`04_search_result.py`](python/04_search_result.py) | Hybrid search → `search_result` → an answer with sources | Yes, 1 call |
| [`05_rag_tool.py`](python/05_rag_tool.py) | Claude calls the search tool on its own | Yes, 2–4 calls |

The collection is [`data/so_tay/`](../../../modules/04-rag/data/so_tay) ("so tay" means handbook): 7 pages from the **fictional** handbook of an environmental lab. The MD-300 meter, the error codes, the device codes and every number are made up. The pages are in Vietnamese on purpose: this module shows how to search a language with accents, and the same steps work for other languages. The English scripts print a short gloss next to each Vietnamese query. The page titles in English:

| File | Title |
|---|---|
| `01_hieu_chuan_ph.md` | Calibrating the pH meter |
| `02_ma_loi_md300.md` | Error codes of the MD-300 multi-parameter meter |
| `03_lay_mau_nuoc.md` | Sampling surface water |
| `04_bao_quan_mau.md` | Storing and transporting samples |
| `05_do_do_quang.md` | Measuring dissolved oxygen with an optical sensor |
| `06_an_toan.md` | Safety when working with water samples |
| `07_quan_ly_thiet_bi.md` | Managing measuring equipment |

The scripts load code from the shared `solutions/` folder. Set `CHAM` to your exercises folder (see "Exercises") and the scripts run with the code you wrote.

In mock mode, the answer does not understand the question. The mock picks the block that shares the most words with the question, so it can return a `search_result_location` citation in the right format. The search part (BM25, RRF) is real code and runs exactly the same with a key.

## 1. The RAG pipeline

```text
Prepare (once)        documents ──▶ split into chunks ──▶ add context ──▶ build the BM25 index
Each question         question ──▶ find top-k ──▶ search_result ──▶ Claude ──▶ answer + citations
```

Each step fails in its own way:

| Step | How it fails |
|---|---|
| Chunking | Chunks too short lose context; too long, they get diluted and cost tokens |
| Indexing | No Unicode normalization, so the same accented letter typed two ways does not match |
| Search | Synonyms ("how often" and "frequency") do not match each other |
| Answer | Claude answers from general knowledge instead of the chunks it was given |

Measure each step on its own. When an answer is wrong, first check whether the right chunk is in the top-k.

## 2. BM25: keyword search

BM25 scores each chunk by the words in the question, based on three ideas:

1. **Rare words are worth more than common words.** "e-17" is in only one chunk, so it scores a lot; "máy" ("machine") is everywhere, so it scores almost nothing. This is the `idf` part.
2. **Repeated words add more, but up to a cap.** A chunk that says "pH" ten times is not much better than one that says it twice. The parameter `k1` controls this saturation.
3. **Long chunks are scored down.** A long chunk holds more words just because it is long. The parameter `b` controls how much.

```text
score(chunk) = Σ  idf(w) · f·(k1 + 1) / (f + k1·(1 − b + b·dl/avgdl))
idf(w)       = ln(1 + (N − n + 0.5) / (n + 0.5))
```

Here `f` is how many times the word `w` appears in the chunk, `dl` is the chunk length, `avgdl` is the average length, `N` is the number of chunks, and `n` is the number of chunks that contain `w`. Common values: `k1 = 1.5`, `b = 0.75`.

**Why BM25, when there are embeddings?** An embedding turns a chunk into a vector by meaning, so it can find "how often" when the document says "frequency". But it easily misses exact strings: the error code `E-17`, the device code `TB-07`, the sample code `SX03-20261012-01`. BM25 matches those strings exactly. Anthropic's blog post uses both and finds the combination better than embeddings alone.

This module uses only BM25, so everything runs on your machine with no extra library and no key. Section 7 covers adding embeddings.

### Tokenizing Vietnamese

BM25 is only as good as its tokenizer. Three points for Vietnamese:

- **Unicode normalization (NFC).** The letter "ệ" can be stored as one character, or as "e" plus two combining marks. Both look the same but are not equal when you compare strings. Always run `unicodedata.normalize("NFC", ...)` before comparing.
- **Keep codes with hyphens and decimal numbers whole.** The regex `\w+(?:[-.,]\w+)*` keeps `e-17`, `md-300` and `7,00` as one token each. Split `e-17` into `e` and `17`, and "e" matches all over the place.
- **Users often type without accents.** "hieu chuan" does not match "hiệu chuẩn" ("calibration"). Build a second index with the accents removed, then merge the two results with RRF (section 5).

Vietnamese is written in syllables: "hiệu chuẩn" is two tokens, "hiệu" and "chuẩn". Syllable-level BM25 still works well for a small collection. Splitting into compound words needs a Vietnamese word segmenter; the repo does not use one.

## 3. Chunking

A chunk is the unit that is searched and sent to Claude. The repo chunks along the markdown structure of the handbook:

- Never merge across a `##` section boundary: a chunk belongs to one section only.
- Within a section, group consecutive paragraphs until you reach a character cap.
- Never cut in the middle of a sentence. A paragraph longer than the cap stands alone.

There is no "right" size. Small chunks make search more precise but lose context more easily; large chunks do the opposite. Measure on real questions.

## 4. Context for chunks

Chunking loses information. The chunk "Thực hiện lại sau mỗi 8 giờ đo, khi đổi điện cực..." ("Repeat after every 8 hours of measuring, when you change the electrode...") does not mention "calibration" or "pH", because those words are in the document title. The question "how often must I recalibrate the pH meter" has a hard time finding it.

**The free way:** copy the title and the section name to the front of the chunk before indexing:

```text
Tài liệu: Hiệu chuẩn máy đo pH. Mục: Tần suất.
Thực hiện lại sau mỗi 8 giờ đo, khi đổi điện cực, ...
```

("Document: Calibrating the pH meter. Section: Frequency.") On the sample handbook, this change alone moves the right chunk from rank 14 to rank 4 ([`02_ngu_canh.py`](python/02_ngu_canh.py)).

**The more expensive way: contextual retrieval.** Send Claude the whole document plus one chunk, ask for 1–2 sentences that place the chunk in context, then put that sentence at the front of the chunk. Anthropic's blog post does this with context sentences of about 50–100 tokens. On their test sets, context for both embeddings and BM25 cut the rate of failed retrievals in the top-20 chunks from 5.7% to 2.9%, and adding a rerank step brought it to 1.9%. Those are 2024 numbers on their data; on your collection you must measure yourself.

One call per chunk, and each call sends the whole document again. For a large collection, use prompt caching for the document part and the Batch API (module 06). Set `effort` to `low` and keep `max_tokens` small: this is a short task done thousands of times. [`03_ngu_canh_claude.py`](python/03_ngu_canh_claude.py) runs it for one document only, to limit the cost.

## 5. Merging several searches: RRF

You have two ranked lists, for example BM25 with accents and BM25 without accents, or BM25 and embeddings. Their scores are not on the same scale, so you cannot add them up. **Reciprocal Rank Fusion** uses only the ranks:

```text
RRF_score(chunk) = Σ over the lists  1 / (k + rank of the chunk in that list)
```

`k = 60` is common. A chunk ranked high in both lists scores the most; a chunk that appears in only one list still has a chance. `rag_mau.tim()` merges BM25 with accents and BM25 without accents this way, so a question typed with or without accents is found either way.

## 6. Giving the results to Claude: `search_result`

You could paste the chunks into the prompt as plain text. A better way is the `search_result` block:

```python
{"type": "search_result",
 "source": "kb://so-tay/02_ma_loi_md300#2",       # a stable ID for the chunk: a URL or an internal ID
 "title": "Mã lỗi máy đo đa chỉ tiêu MD-300 — Lỗi điện cực",
 "content": [{"type": "text", "text": "E-17: điện cực khô ..."},
             {"type": "text", "text": "E-18: điện cực không phản hồi ..."}],
 "citations": {"enabled": True}}
```

(The title means "Error codes of the MD-300 multi-parameter meter — Electrode errors"; E-17 is "dry electrode", E-18 is "electrode not responding".) With citations on, each claim in the answer points back to the text block it used:

```text
citation: type="search_result_location", source="kb://so-tay/02_ma_loi_md300#2",
          search_result_index=0, start_block_index=0, end_block_index=1, cited_text="E-17: ..."
```

Rules to remember (docs: Search results; `claude_vi` blocks these first):

- `source`, `title` and `content` are required. `content` holds only text blocks with text in them, no images.
- Claude cites **whole** text blocks, never part of a block. For tighter citations, split `content` into smaller blocks: the repo uses one block per line.
- `search_result_index` counts from 0 over every `search_result` block in the request, in order of appearance, including those inside a `tool_result`.
- Citations are on for all of them or for none.
- A `search_result` goes only in a user turn (including inside a `tool_result`), never in an assistant turn.
- `cited_text` does not count as output tokens.
- Do not write "return only JSON" when you want citations: the request runs, but there may be almost no citations (module 05).

Compared with the `document` block of module 05: `document` is for one whole document (a PDF, a text), and the API splits the sentences for you. `search_result` is for chunks you found yourself, with a `source` and `title` you set. That is what you need to show a "view source" link.

In `system`, say clearly that Claude must answer only from the search results, and must say "no information" when nothing was found, with the reason. [`04_search_result.py`](python/04_search_result.py) does exactly this.

### Let Claude search on its own

Script 04 always searches first, then asks. [`05_rag_tool.py`](python/05_rag_tool.py) turns the search into a tool. Claude decides whether it needs to search, picks the keywords, and searches again if it does not have enough. The tool returns a list of `search_result` blocks in the `tool_result`:

- If a `tool_result` holds one `search_result`, every block inside it must be a `search_result`. To add a note, put it in the `content` of a `search_result`.
- If nothing is found, return a text block like "No chunk found." instead of raising an error, so Claude can explain it to the user.
- Keep `tool_choice` at `auto`. The Search results docs have an example that forces the tool call with `tool_choice`, but `any`/`tool` returns 400 on Opus 5.5, Sonnet 5.5 and Fable 5.x. To be sure Claude searches, use script 04: search first, in code.

## 7. Going further: add local embeddings

BM25 does not understand synonyms: "how often" does not match "frequency". An embedding model running on your machine covers this gap. How to plug it into this module's code:

1. Install an embedding library and a multilingual model that supports your language (download it once, then it runs offline).
2. Encode every chunk (with its context added) into a vector once, and store it.
3. For each question: encode the question and take the top-20 chunks by cosine similarity.
4. Merge that list with the BM25 list using `hop_nhat_rrf` from exercise 3. Everything else stays the same.

The repo does **not** ship this part, because embedding libraries usually pull in PyTorch (hundreds of MB) and CI would have to download a model. Before you add it to a real project, measure whether it helps on your questions: for a collection full of codes and terms, BM25 plus context may be enough.

Anthropic has no embedding API of its own. The Embeddings docs point to outside providers; using one needs another kind of key.

## Common traps

- **Building RAG when the collection is small enough to send whole.** Measure the cost of both ways first.
- **No Unicode normalization.** Two ways of typing "ệ" do not match, and search results become erratic.
- **Splitting `E-17` into `e` and `17`.**
- **Ignoring users who type without accents.**
- **Cutting a chunk mid-sentence, or merging across section boundaries.**
- **Chunks that lost their context** ("repeat after every 8 hours" without saying what to repeat).
- **Adding BM25 scores to embedding scores.** Different scales. Use RRF.
- **Taking too few chunks.** The right chunk is at rank 4 and you send only the top 3, so Claude never sees it. The blog post found top-20 better than top-5 and top-10 on their data.
- **Pasting chunks into the prompt as plain text** and asking Claude to cite sources itself. Use `search_result` + citations.
- **Mixing `search_result` with text in the same `tool_result`** → 400.
- **Forcing the search tool with `tool_choice` `any`** → 400 on many 5.x models.
- **No "if there is no information, say so" sentence** in `system`. Claude fills the gap with general knowledge.
- **Putting retrieved content in a `system` message.** It is outside data, not instructions (module 07).

## What changed with 5.x models

| Before | Now |
|---|---|
| Paste chunks into the prompt and ask the model to write "[source 2]" | `search_result` blocks + citations: the API returns the `source` and the block position, and `cited_text` costs no output tokens |
| Force the search tool with `tool_choice` `any` | 400 on Opus 5.5, Sonnet 5.5, Fable 5.x; search first in code, or keep `auto` |
| Prefill "According to the documents," to keep Claude on the documents | Prefill returns 400; say it clearly in `system` |
| Chunk context generated with Claude 3 Haiku (the 2024 blog post) | Haiku 5.5 with effort `low`; Claude 3 Haiku retired on 2026-04-20 |

## Exercises

```bash
CHAM="$PWD/en/modules/04-rag/exercises" uv run pytest modules/04-rag -q
```

| Exercise | Content |
|---|---|
| [`bai1_bm25.py`](exercises/bai1_bm25.py) | Tokenize Vietnamese (NFC, remove accents, keep codes whole), BM25 by the exact formula |
| [`bai2_chia_doan.py`](exercises/bai2_chia_doan.py) | Chunk by section, add the title and section, a request asking Claude to write the context |
| [`bai3_hop_nhat.py`](exercises/bai3_hop_nhat.py) | RRF, packing `search_result` blocks, reading `search_result_location` |

When all three are done, run the scripts again with the same `CHAM` to see the whole pipeline run on your code. Solutions are in [`solutions/`](../../../modules/04-rag/solutions/). Check yourself: [quiz.md](quiz.md). Sources: [references.md](references.md).

## Next

Module 05, Structured outputs, PDF and Citations. If you have done 05 already, go on to module 06, Cost, where prompt caching makes the contextual retrieval step much cheaper.
