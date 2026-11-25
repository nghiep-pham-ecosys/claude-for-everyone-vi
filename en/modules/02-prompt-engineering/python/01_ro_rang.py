"""Module 02: clear, direct, and say "why" (ro_rang = clear).

Claude is like a capable colleague who just joined: it does not know your habits.
The more specific the prompt (format, length, reader, reason), the closer the result.

Run:  CLAUDE_MOCK=1 uv run python en/modules/02-prompt-engineering/python/01_ro_rang.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))

from claude_vi import ClaudeVi, text_of  # noqa: E402

client = ClaudeVi()

vague = "Summarize this article."

clear = """Summarize the article below for first-year environmental science students.

Requirements:
1. Exactly 3 sentences, each under 25 words.
2. Sentence one gives the research question, sentence two the method, sentence three the main result with a number.
3. Explain technical terms in plain words, because the readers have not taken this course yet.

<article>
The study measured PM2.5 at 12 stations in Hanoi during 2025. Stations near major roads
had a yearly average of 48 µg/m³, 1.6 times higher than stations in residential areas.
</article>"""

# A reason in system helps Claude work out the rules you did not write
system = (
    "You write study materials. The answer will be printed on a slide, "
    "so do not use markdown, and do not open with a lead-in like 'Here is...'."
)

for name, prompt in [("Vague", vague), ("Clear", clear)]:
    msg = client.ask(prompt, system=system)
    print(f"=== {name} ({len(prompt)} prompt characters)\n{text_of(msg)}\n")

print("In mock mode both answers are the same. Run for real to see the difference; the lesson here is the prompt.")
