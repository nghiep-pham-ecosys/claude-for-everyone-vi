"""Exercise 2: read the citations of three document types, and check them yourself.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
kiem_trich_dan = check citations, doc_trich_dan = read citations, trich_dan = citation, tai_lieu = documents,
khang_dinh = claim, vi_tri = location, hop_le = valid, ly_do = reason, trang_pdf = PDF pages.

The API makes sure a citation points into the document you sent. This exercise checks that again in code,
because (1) you will store and show citation locations to users, and (2) the response can go through
several layers (cache, log, fixture) before it reaches you.

doc_trich_dan(msg, tai_lieu) -> list[TrichDan]
    tai_lieu: the list of document blocks you SENT, in order (document_index counts from 0 across every
    document in the request). For each citation in each text block of msg, make one TrichDan:
    - khang_dinh = block.text, cited_text, tai_lieu = document_index
    - vi_tri: "ký tự {start}–{end}" | "trang {start}–{end}" | "khối {start}–{end}"
      (these exact Vietnamese strings: "ký tự" = characters, "trang" = pages, "khối" = blocks)
    - hop_le / ly_do by type:
        char_location           the document is plain text and data[start:end] == cited_text
        page_location           the document is a PDF; 1 <= start < end <= page_count + 1 (end excluded);
                                cited_text (with whitespace normalized) is in the text of those pages
        content_block_location  the document is custom content; 0 <= start < end <= block_count;
                                cited_text (normalized) is in the text of those blocks
        document_index outside the list -> hop_le=False
    - stop_reason other than "end_turn" -> raise ValueError.

trang_pdf(doc) is already written.

Grade:  CHAM="$PWD/en/modules/05-structured-pdf-citations/exercises" uv run pytest modules/05-structured-pdf-citations -q
"""
from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from typing import Any

from anthropic.types import Message


@dataclass(frozen=True)
class TrichDan:
    khang_dinh: str          # the text of the block that holds the citation
    cited_text: str
    tai_lieu: int            # document_index
    vi_tri: str              # "ký tự 10–42", "trang 1–2", "khối 0–1"
    hop_le: bool
    ly_do: str | None = None


def trang_pdf(doc: dict[str, Any]) -> list[str]:
    """The text of each page of a base64 PDF document (page 1 at index 0)."""
    from pypdf import PdfReader

    data = base64.b64decode(doc["source"]["data"])
    return [p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages]


def doc_trich_dan(msg: Message, tai_lieu: list[dict[str, Any]]) -> list[TrichDan]:
    raise NotImplementedError("TODO: exercise 2")
