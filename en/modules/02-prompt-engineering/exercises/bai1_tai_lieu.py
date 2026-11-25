"""Exercise 1: build a multi-document prompt.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
tao_prompt_tai_lieu = build the document prompt, tai_lieu = documents, nguon = source,
noi_dung = content, cau_hoi = question.

tao_prompt_tai_lieu(tai_lieu, cau_hoi) -> str
    tai_lieu: a list of (nguon, noi_dung). Empty -> raise ValueError.
    The result looks like this (in the same order, index counted from 1):

    <documents>
    <document index="1">
    <source>nguon</source>
    <document_content>
    noi_dung
    </document_content>
    </document>
    ... (the next documents)
    </documents>

    <question>
    cau_hoi
    </question>

Why: long documents FIRST and the question LAST give better results; XML tags keep data and question apart.

Grade:  CHAM="$PWD/en/modules/02-prompt-engineering/exercises" uv run pytest modules/02-prompt-engineering -q
"""
from __future__ import annotations


def tao_prompt_tai_lieu(tai_lieu: list[tuple[str, str]], cau_hoi: str) -> str:
    raise NotImplementedError("TODO: exercise 1")
