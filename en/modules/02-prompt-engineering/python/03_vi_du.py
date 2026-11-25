"""Module 02: teach with examples (few-shot / multishot prompting; vi_du = examples).

A few good examples are the surest way to fix the format and the tone.
The docs advise 3–5 examples, close to the real data, varied enough, wrapped in <example>.

Run:  CLAUDE_MOCK=1 uv run python en/modules/02-prompt-engineering/python/03_vi_du.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))

from claude_vi import ClaudeVi, text_of  # noqa: E402

examples = [
    ("The lectures are easy to follow, but the lab has no pH meter.", "facilities"),
    ("The teacher explains again when the class is lost. Very patient.", "teaching"),
    ("The midterm had a question outside the material we covered.", "assessment"),
    ("Everything is fine.", "other"),  # a "hard" example: it fits no group clearly
]
example_block = "\n".join(
    f"<example>\n<feedback>{text}</feedback>\n<group>{group}</group>\n</example>" for text, group in examples
)

system = (
    "You sort student feedback into exactly one group: "
    "teaching, assessment, facilities, other. Return only the group name."
)
prompt = f"""<examples>
{example_block}
</examples>

<feedback>The projector in room B2 is blurry; from the back row you cannot read the slides.</feedback>"""

print(prompt, "\n")
msg = ClaudeVi().ask(prompt, system=system)
print("Group:", text_of(msg))
print("\nWant to be sure the output is one of the 4 groups? Use structured outputs (script 04).")
