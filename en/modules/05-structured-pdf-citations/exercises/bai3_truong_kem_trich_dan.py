"""Exercise 3: one line per field, and each line has a citation.

The names stay in Vietnamese because the same tests grade the Vietnamese and the English files:
truong = fields, tai_lieu = document, yeu_cau_truong = field request, tach_truong = split fields,
ket_qua = result, gia_tri = value, trich_dan = citations, truong_thieu = missing fields.

Citations cannot be used together with structured outputs. The way the docs suggest: ask for each field
on its own line as "name: value", with a source for each line, then split it yourself.

yeu_cau_truong(tai_lieu, truong) -> a dict of parameters for client.create(**...)
    - Turn on citations on the document (citations.enabled = True), and put the document BEFORE the question.
    - The prompt names every field, asks for one line per field as "name: value", a source for each line,
      and only the value after the colon.
    - NO output_config (it would be a 400), and do NOT write "return only JSON" (the request runs, but
      almost all citations are lost).
    - empty truong -> raise ValueError.

tach_truong(msg, truong) -> {name: {"gia_tri": str, "trich_dan": [cited_text, ...]}}
    Following the algorithm in the docs:
    1. Read the text blocks in order, append the text to the current line; on "\\n", start a new line.
    2. Attach the citations of a block to EVERY line that holds part of that block's text.
    3. Drop lines with no colon. Split at the FIRST colon (a value like "08:20" stays whole),
       and strip spaces at both ends. Drop lines whose name is not in `truong`. If a name repeats,
       keep the first one.
    - stop_reason other than "end_turn" -> raise ValueError.

truong_thieu(ket_qua, truong) -> list[str]
    The fields (in the order of `truong`) that are missing, have an empty value, or have no citation.
    The API does not promise that every field has a value and a citation: you must check it yourself.

Grade:  CHAM="$PWD/en/modules/05-structured-pdf-citations/exercises" uv run pytest modules/05-structured-pdf-citations -q
"""
from __future__ import annotations

from typing import Any

from anthropic.types import Message


def yeu_cau_truong(tai_lieu: dict[str, Any], truong: list[str]) -> dict[str, Any]:
    raise NotImplementedError("TODO: exercise 3")


def tach_truong(msg: Message, truong: list[str]) -> dict[str, dict[str, Any]]:
    raise NotImplementedError("TODO: exercise 3")


def truong_thieu(ket_qua: dict[str, dict[str, Any]], truong: list[str]) -> list[str]:
    raise NotImplementedError("TODO: exercise 3")
