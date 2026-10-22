"""Split a pasted job ad into passages and keep the ones that describe the job (spec Story 4).

Headings ("Arbetsuppgifter", "What we offer", …) label the passages under them. Passages outside
any heading take the label of the nearest anchor centroid, using the embedder search already has
loaded. No LLM and no network (FR-022).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import numpy as np
import yaml
from pydantic import BaseModel, Field

from lonekrav.core.embeddings import Embedder

Label = Literal["title", "duty", "skill", "company", "benefits", "other"]
KEEP = {"title", "duty", "skill"}
ANCHORS_FILE = Path(__file__).with_name("adparse_anchors.yaml")
MAX_TITLE_WORDS = 10

HEADINGS: dict[str, Label] = {h: label for label, hs in {
    "duty": ["arbetsuppgifter", "dina arbetsuppgifter", "om tjänsten", "om rollen", "i rollen",
             "ansvarsområden", "responsibilities", "key responsibilities", "your role",
             "the role", "about the role", "what you will do", "your tasks", "duties"],
    "skill": ["kvalifikationer", "vi söker dig som", "vem är du", "din profil", "krav",
              "meriterande", "requirements", "qualifications", "who you are", "your profile",
              "what we're looking for", "what we are looking for", "skills", "experience"],
    "company": ["om oss", "om företaget", "vilka är vi", "about us", "about the company",
                "who we are"],
    "benefits": ["vi erbjuder", "förmåner", "what we offer", "we offer", "benefits",
                 "why join us"],
    "other": ["ansökan", "övrigt", "kontakt", "praktisk information", "how to apply",
              "contact", "practical information", "application"],
}.items() for h in hs}

_BULLET = re.compile(r"^\s*(?:[-•*–·]|\d+[.)])\s+")
_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-ZÅÄÖ])")


class AdPassage(BaseModel):
    index: int
    text: str
    label: Label
    keep: bool
    by: Literal["heading", "anchor", "position"]


class AdText(BaseModel):
    text: str = Field(min_length=1, max_length=20_000)


class ParsedAd(BaseModel):
    passages: list[AdPassage]
    kept_text: str
    fallback_to_whole: bool


def _heading(line: str) -> Label | None:
    return HEADINGS.get(line.strip().rstrip(":").strip().casefold())


def _sentences(line: str) -> list[str]:
    """A line with its bullet stripped, split into sentences."""
    return [s for s in _SENTENCE.split(_BULLET.sub("", line).strip()) if s]


def _is_title(line: str) -> bool:
    words = line.split()
    return 0 < len(words) <= MAX_TITLE_WORDS and not line.rstrip().endswith((".", "!", "?"))


_CENTROIDS: dict[str, tuple[list[str], np.ndarray]] = {}


def _centroids(embedder: Embedder, anchors: dict[str, list[str]] | None):
    key = embedder.identity
    if anchors is None and key in _CENTROIDS:
        return _CENTROIDS[key]
    use = anchors or yaml.safe_load(ANCHORS_FILE.read_text())
    labels = list(use)
    vecs = [embedder.encode_documents(use[lab]).mean(axis=0) for lab in labels]
    m = np.stack(vecs)
    m /= np.linalg.norm(m, axis=1, keepdims=True)
    if anchors is None:
        _CENTROIDS[key] = (labels, m)
    return labels, m


def parse(text: str, embedder: Embedder, anchors: dict[str, list[str]] | None = None) -> ParsedAd:
    rows: list[tuple[str, Label | None, str]] = []  # (text, label or None for anchors, by)
    section: Label | None = None
    lines = [ln for ln in text.splitlines() if ln.strip()]
    for i, line in enumerate(lines):
        if (h := _heading(line)) is not None:
            section = h
            continue
        if i == 0 and _is_title(line):
            rows.append((line.strip(), "title", "position"))
            continue
        for s in _sentences(line):
            rows.append((s, section, "heading") if section else (s, None, "anchor"))

    todo = [i for i, (_, label, _) in enumerate(rows) if label is None]
    if todo:
        labels, cents = _centroids(embedder, anchors)
        v = embedder.encode_queries([rows[i][0] for i in todo])
        v /= np.linalg.norm(v, axis=1, keepdims=True) + 1e-12
        for i, best in zip(todo, (v @ cents.T).argmax(axis=1), strict=True):
            rows[i] = (rows[i][0], labels[best], "anchor")

    passages = [AdPassage(index=i, text=t, label=lab, keep=lab in KEEP, by=by)
                for i, (t, lab, by) in enumerate(rows)]
    kept = "\n".join(p.text for p in passages if p.keep)
    return ParsedAd(passages=passages, kept_text=kept or text, fallback_to_whole=not kept)
