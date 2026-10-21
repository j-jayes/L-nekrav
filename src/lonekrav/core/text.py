"""Text analysis for BM25: Swedish stemming and compound splitting.

Milvus Lite's analyzer only lowercases and splits on non-word characters, which leaves Swedish
compounds ("backendutvecklare") and inflections ("sjuksköterskor") unmatched. Indexed text and
queries both go through `analyze`, so they always agree.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable
from functools import cache

import snowballstemmer

WORD = re.compile(r"\w+")
MIN_PART = 4  # shortest compound part considered
_SV = snowballstemmer.stemmer("swedish")
_EN = snowballstemmer.stemmer("english")


@cache
def _stems(word: str) -> tuple[str, ...]:
    """Swedish and English stems: queries and documents come in either language."""
    return tuple(dict.fromkeys((_SV.stemWord(word), _EN.stemWord(word))))


def build_vocab(texts: Iterable[str], min_count: int = 1) -> frozenset[str]:
    """Words long enough to be compound parts, taken from the indexed corpus."""
    counts = Counter(w for t in texts for w in WORD.findall(t.lower()) if len(w) >= MIN_PART)
    words = {w for w, n in counts.items() if n >= min_count}
    return frozenset(words | {s for w in words if len(s := _SV.stemWord(w)) >= MIN_PART})


def _split(word: str, vocab: frozenset[str]) -> list[str]:
    """Split a closed compound into two vocabulary words, allowing a linking 's'."""
    for i in range(len(word) - MIN_PART, MIN_PART - 1, -1):  # prefer the longest head
        head, tail = word[:i], word[i:]
        if tail not in vocab and _SV.stemWord(tail) not in vocab:  # tail may be inflected
            continue
        if head in vocab:
            return [head, tail]
        if head.endswith("s") and head[:-1] in vocab:
            return [head[:-1], tail]
    return []


def analyze(text: str, vocab: frozenset[str] = frozenset()) -> str:
    """Space-separated stems, with compound parts added after the full word's stems."""
    out: list[str] = []
    for w in WORD.findall(text.lower()):
        out += _stems(w)
        if len(w) >= 2 * MIN_PART and w not in vocab:
            for part in _split(w, vocab):
                out += _stems(part)
    return " ".join(out)


def profile_vocab(profiles: Iterable) -> frozenset[str]:
    """Compound-part vocabulary from committed profiles' titles and synonyms. Index and query
    time both derive it from the same committed file, so they always agree."""
    return build_vocab(t for p in profiles for t in (p.title_sv, p.title_en,
                                                      *(s.label for s in p.synonyms)))
