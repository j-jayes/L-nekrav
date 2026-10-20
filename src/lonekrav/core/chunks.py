"""Split an occupation profile into searchable text chunks (research R7).

KBLab truncates at 384 tokens, so one vector per profile would lose most of its text.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel

from lonekrav.core.models import OccupationProfile

MAX_CHARS = 2000
MAX_LABELS = 40


class Chunk(BaseModel):
    chunk_id: str
    code: str
    kind: Literal["title", "desc_sv", "desc_en", "synonyms_sv", "synonyms_en"]
    lang: Literal["sv", "en", "mixed"]
    text: str


def _split(text: str, limit: int = MAX_CHARS) -> list[str]:
    """Split on sentence ends so each piece fits within `limit` characters."""
    pieces, cur = [], ""
    for sentence in re.split(r"(?<=[.;:])\s+", text.strip()):
        while len(sentence) > limit:  # a single overlong sentence: hard split
            pieces.append(sentence[:limit])
            sentence = sentence[limit:]
        if cur and len(cur) + 1 + len(sentence) > limit:
            pieces.append(cur)
            cur = sentence
        else:
            cur = f"{cur} {sentence}".strip()
    if cur:
        pieces.append(cur)
    return pieces


def chunk_profile(p: OccupationProfile, holdout: set[str] = frozenset()) -> list[Chunk]:
    """`holdout`: case-folded titles used as benchmark queries, kept out of the indexed text."""
    chunks: list[Chunk] = []

    def add(kind, lang, text):
        n = sum(c.kind == kind for c in chunks)
        chunks.append(Chunk(chunk_id=f"{p.code}:{kind}:{n}", code=p.code, kind=kind, lang=lang,
                            text=text))

    add("title", "mixed", f"{p.title_sv} / {p.title_en}")
    for d in p.descriptions:
        for piece in _split(d.text):
            add(f"desc_{d.lang}", d.lang, piece)
    for lang in ("sv", "en"):
        labels = [s.label for s in p.synonyms
                  if s.lang == lang and s.label.casefold().strip() not in holdout]
        for i in range(0, len(labels), MAX_LABELS):
            add(f"synonyms_{lang}", lang, "; ".join(labels[i:i + MAX_LABELS]))
    return chunks
