"""FR-013a / research R4: a slash-joined list of titles is searched as alternatives."""

import pytest

from lonekrav.core.search import title_parts


@pytest.mark.parametrize("text,parts", [
    ("Aktuarie/Försäkringsaktuarie/Försäkringsmatematiker",
     ["Aktuarie", "Försäkringsaktuarie", "Försäkringsmatematiker"]),
    ("Game designer / Speldesigner", ["Game designer", "Speldesigner"]),
    ("Arbetsledare, kontorspersonal/Gruppledare, kontorspersonal",
     ["Arbetsledare, kontorspersonal", "Gruppledare, kontorspersonal"]),
    ("backend developer", None),
    ("We build and/or test apps. Then we ship them.", None),  # prose: sentence punctuation
    ("Utvecklare/Tester\nAnsvara för drift", None),  # a line break: an ad, not a title list
    ("senior software engineer working on payments infrastructure/backend", None),  # > 6 words
    ("/", None),
    ("Utvecklare/", None),
])
def test_title_parts(text, parts):
    assert title_parts(text) == parts
