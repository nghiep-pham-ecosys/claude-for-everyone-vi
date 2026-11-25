# Claude for Everyone (English edition)

[Tiếng Việt](../README.md) · **English**

> An **unofficial** learning path for the Claude platform by Anthropic, from your first API call to multi-agent systems.
>
> A community project, **not affiliated with or endorsed by Anthropic**. "Claude" and "Anthropic" are trademarks of Anthropic PBC.

## About this edition

The course was first written in Vietnamese. This folder is the English edition. It mirrors the Vietnamese modules one to one: the same sections, the same examples, the same exercises and the same checked facts. The English text is also the script for the English videos, so the sentences are short and plain.

Modules 00 to 04 are translated. Modules 05 to 10 are still Vietnamese only; they link to the Vietnamese pages below until their translation lands.

How the English edition is built:

- **Lessons** (`README.md`, `quiz.md`, `references.md`) are translated into English under `en/modules/`.
- **Example scripts** that print Vietnamese text have an English copy under `en/modules/NN-name/python/`, with the same file name and the same logic. Scripts with no text for the reader are shared, not copied.
- **Exercises** have an English copy under `en/modules/NN-name/exercises/`. Function and class names stay the same as in the Vietnamese files, because the same tests grade both. Each English module says how to grade your English exercise file.
- **Code that the scripts share** (the `claude_vi` wrapper, the tests, the sample data) lives once, in the main repo. Some messages from `claude_vi` and from the mock are still in Vietnamese.
- Fact check dates and sources stay the same as in the Vietnamese edition.

## Start in 5 minutes (no API key)

```bash
git clone https://github.com/nghiep-pham-ecosys/claude-for-everyone-vi.git && cd claude-for-everyone-vi
uv sync
CLAUDE_MOCK=1 uv run python en/modules/01-messages-api/python/01_hello.py
```

Have a key? Copy `.env.example` to `.env`, fill in `ANTHROPIC_API_KEY`, and drop `CLAUDE_MOCK=1`.

## Learning path

Legend: ✅ done · 🇻🇳 Vietnamese only for now · 🤝 open to community contributions.

| Level | Module | English |
|---|---|---|
| Basic | [00 Setup](modules/00-setup/README.md) | ✅ |
| Basic | [01 Messages API](modules/01-messages-api/README.md) | ✅ |
| Basic | [02 Prompt engineering](modules/02-prompt-engineering/README.md) | ✅ |
| Intermediate | [03 Tool use](modules/03-tool-use/README.md) | ✅ |
| Intermediate | [04 RAG](modules/04-rag/README.md) | ✅ |
| Intermediate | [05 Structured outputs, PDF and Citations](../modules/05-structured-pdf-citations/README.md) | 🇻🇳 |
| Intermediate | [06 Cost](../modules/06-cost/README.md) | 🇻🇳 |
| Intermediate | [07 Thinking](../modules/07-thinking/README.md) | 🇻🇳 |
| Advanced | [08 Agents & workflows](../modules/08-agents-workflows/README.md) | 🇻🇳 |
| Advanced | [09 Agent SDK](../modules/09-agent-sdk/README.md) | 🇻🇳 |
| Advanced | [10 MCP](../modules/10-mcp/README.md) | 🇻🇳 |
| Open to the community | 11 Claude Code · 12 Agent Skills · 13 Evals · 14 Production · 15 Research | 🤝 |

Suggested order: 00 → 01 → 02 → 03 → 05 → 07 → 04 → 06 → 08 → 09 → 10. Why: module 04 is best after 05, module 06 needs 07, module 08 needs 03 and 07, module 09 needs 08, and module 10 needs 09 (see "Needs" at the top of each module).

## Three rules of this repo

1. **Every model ID lives in [`config/models.yaml`](../config/models.yaml).** CI blocks unknown or retired models.
2. **Every call goes through [`claude_vi`](../shared/py/claude_vi).** The wrapper stops requests that would fail with a 400 error on 5.x models before they are sent. It also has a mock mode, so CI costs nothing.
3. **No copying of content under restrictive licenses.** See [NOTICE.md](../NOTICE.md). The English text is translated from this repo's own Vietnamese text only.

## Cost

The default model is `claude-haiku-5-5` with `MAX_TOKENS=1024`. Each module README gives an estimated cost. The function `estimate_cost_usd(msg)` computes it from the real `usage`.

## Contributing

The repo is open to everyone, and you do not need an API key: everything runs in mock mode. Read [CONTRIBUTING.md](../CONTRIBUTING.md) (in Vietnamese). Translating modules 05 to 10 is a good first contribution: follow the layout of `en/modules/01-messages-api/`, and run `CLAUDE_MOCK=1 uv run pytest -q tests/test_english_edition.py` to check that your module mirrors the Vietnamese one.

## License

Code: [MIT](../LICENSE). Course content: [CC BY 4.0](../LICENSE-CONTENT).
