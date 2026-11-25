"""Exercise 2: a few-shot example block.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
tao_khoi_vi_du = build the example block, vi_du = examples, dau_vao = input, dau_ra = output.

tao_khoi_vi_du(vi_du) -> str
    vi_du: a list of (dau_vao, dau_ra).
    - Fewer than 3 or more than 5 examples -> raise ValueError (the docs advise 3–5).
    - Every example has the same dau_ra -> raise ValueError (not varied: Claude learns "always answer X").
    - The result:

    <examples>
    <example>
    <input>dau_vao</input>
    <output>dau_ra</output>
    </example>
    ...
    </examples>

Grade:  CHAM="$PWD/en/modules/02-prompt-engineering/exercises" uv run pytest modules/02-prompt-engineering -q
"""
from __future__ import annotations


def tao_khoi_vi_du(vi_du: list[tuple[str, str]]) -> str:
    raise NotImplementedError("TODO: exercise 2")
