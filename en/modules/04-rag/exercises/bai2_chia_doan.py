"""Exercise 2: split documents into chunks and add context.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
chia_doan = split into chunks, them_ngu_canh = add context, yeu_cau_ngu_canh = context request,
TaiLieu = document (ten = name, noi_dung = content), Doan = chunk (tieu_de = title, muc = section),
max_ky_tu = maximum characters.

chia_doan(tai_lieu, max_ky_tu=400) -> list[Doan]
    The document is markdown: one "# Title" line, "## Section" lines, paragraphs separated by blank lines.
    - The part before the first "##" section is a part with muc = "".
    - Within each section, group consecutive paragraphs (joined with "\\n\\n") while the total length stays
      ≤ max_ky_tu. If adding one more paragraph goes over, close the current Doan and open a new one.
      A paragraph longer than max_ky_tu still stands alone; do NOT cut it mid-sentence.
    - Do not group across section boundaries. A section with no text makes no Doan.
    - id = "{tai_lieu.ten}#{n}", with n counted from 1 in document order. The "#"/"##" lines are not in noi_dung.

them_ngu_canh(doan) -> str
    "Tài liệu: {tieu_de}. Mục: {muc}.\\n{noi_dung}"; if muc is empty, leave out " Mục: ...".
    ("Tài liệu" means document and "Mục" means section. The prefix stays in Vietnamese because the
    handbook is in Vietnamese.) This is the free way to add context: copy the title and section name to
    the front of the chunk before indexing.

yeu_cau_ngu_canh(tai_lieu, doan) -> dict of parameters for client.create(**...)
    Ask Claude to write 1–2 context sentences for the chunk (contextual retrieval):
    - one user turn: the whole document in <document>...</document> FIRST, then the chunk in <chunk>...</chunk>,
      then the instruction to return only the context sentence;
    - "max_tokens" ≤ 256 and "output_config": {"effort": "low"}: a short task, done for thousands of chunks.

Grade:  CHAM="$PWD/en/modules/04-rag/exercises" uv run pytest modules/04-rag -q
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TaiLieu:
    ten: str          # the file name without extension, for example "01_hieu_chuan_ph"
    noi_dung: str     # the full markdown


@dataclass(frozen=True)
class Doan:
    id: str           # "{ten}#{number from 1}"
    tieu_de: str      # the "# ..." line of the document
    muc: str          # the "## ..." line that holds the chunk; "" if the chunk is before the first section
    noi_dung: str


def chia_doan(tai_lieu: TaiLieu, max_ky_tu: int = 400) -> list[Doan]:
    raise NotImplementedError("TODO: exercise 2")


def them_ngu_canh(doan: Doan) -> str:
    raise NotImplementedError("TODO: exercise 2")


def yeu_cau_ngu_canh(tai_lieu: TaiLieu, doan: Doan) -> dict[str, Any]:
    raise NotImplementedError("TODO: exercise 2")
