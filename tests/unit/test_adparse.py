"""Job-ad parsing (spec Story 4, FR-021–FR-023): split, label, keep only what describes the job."""

import socket

import pytest

from lonekrav.core.adparse import parse
from lonekrav.core.embeddings import FakeEmbedder

AD = """Senior Backend Developer

About us
Acme is a fintech company in Stockholm. We have 60 employees.

Responsibilities
- Build REST APIs in Python
- Review code

Requirements
• Five years of Python experience

What we offer
- Six weeks of vacation
"""

ANCHORS = {  # tiny anchors the FakeEmbedder (bag of words) can tell apart
    "duty": ["you will build and maintain systems"],
    "skill": ["experience and knowledge required"],
    "company": ["our company was founded and has employees"],
    "benefits": ["we offer vacation pension and allowance"],
}


def labels(parsed):
    return [(p.text, p.label, p.keep) for p in parsed.passages]


def test_bullets_are_stripped_and_long_lines_split_into_sentences():
    ad = "Title\n\nResponsibilities\n- one\n• two\n1. three\nFirst sentence here. Second one."
    p = parse(ad, FakeEmbedder(), anchors=ANCHORS)
    assert [x.text for x in p.passages] == ["Title", "one", "two", "three", "First sentence here.",
                                            "Second one."]


def test_headings_label_what_follows_and_are_not_passages():
    p = parse(AD, FakeEmbedder(), anchors=ANCHORS)
    assert labels(p) == [
        ("Senior Backend Developer", "title", True),
        ("Acme is a fintech company in Stockholm.", "company", False),
        ("We have 60 employees.", "company", False),
        ("Build REST APIs in Python", "duty", True),
        ("Review code", "duty", True),
        ("Five years of Python experience", "skill", True),
        ("Six weeks of vacation", "benefits", False),
    ]
    assert {x.by for x in p.passages} == {"position", "heading"}
    assert p.kept_text.splitlines() == ["Senior Backend Developer", "Build REST APIs in Python",
                                        "Review code", "Five years of Python experience"]


def test_swedish_headings():
    ad = "Utvecklare\n\nOm oss\nVi är en bank.\n\nArbetsuppgifter\n- Utveckla system\n\n" \
         "Kvalifikationer\n- Erfarenhet av Java\n\nVi erbjuder\n- Friskvårdsbidrag\n"
    got = [(p.label, p.keep) for p in parse(ad, FakeEmbedder(), anchors=ANCHORS).passages]
    assert got == [("title", True), ("company", False), ("duty", True), ("skill", True),
                   ("benefits", False)]


def test_an_unknown_heading_ends_the_section_before_it():
    """Found by hand in Feature 004: a Swedish ad's "Om tjänsten" made everything after it a duty,
    because the headings that followed ("Dina förmåner som anställd", "Din arbetsplats") are not in
    the list. An unknown heading-like line now ends the section, and anchors label what follows."""
    ad = ("Sjuksköterska\n\nOm tjänsten\n- Du vårdar patienter\n- Du övervakar vitala parametrar\n\n"
          "Dina förmåner som anställd\nWe offer vacation pension and allowance to all staff.\n")
    p = parse(ad, FakeEmbedder(), anchors=ANCHORS)
    assert [(x.text, x.label, x.by) for x in p.passages[1:3]] == [
        ("Du vårdar patienter", "duty", "heading"), ("Du övervakar vitala parametrar", "duty", "heading")]
    assert (p.passages[-1].label, p.passages[-1].by) == ("benefits", "anchor")
    assert p.passages[-1].keep is False


def test_unheaded_passages_take_the_nearest_anchor():
    ad = "Cook\n\nWe offer vacation pension and allowance to all staff.\nYou will build and maintain menus."
    p = parse(ad, FakeEmbedder(), anchors=ANCHORS)
    assert [(x.label, x.by) for x in p.passages[1:]] == [("benefits", "anchor"), ("duty", "anchor")]


def test_long_first_line_is_not_a_title():
    p = parse("We are looking for an experienced developer who loves building great products.",
              FakeEmbedder(), anchors=ANCHORS)
    assert p.passages[0].label != "title"


def test_nothing_kept_falls_back_to_the_whole_ad():
    ad = "About us\nAcme is great.\n\nWhat we offer\n- Pension"
    p = parse(ad, FakeEmbedder(), anchors=ANCHORS)
    assert p.fallback_to_whole and p.kept_text == ad


def test_parsing_makes_no_network_call(monkeypatch):  # FR-022
    def blocked(*a, **k):
        raise AssertionError("network access during parsing")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    assert parse(AD, FakeEmbedder()).passages  # default anchors from the committed YAML


@pytest.mark.parametrize("name", ["en1_backend.txt", "sv4_forskollarare.txt"])
def test_fixture_ads_split_into_their_labelled_passages(fixtures, name):
    import yaml

    gold = yaml.safe_load((fixtures / "ads/labels.yaml").read_text())[name]["passages"]
    parsed = parse((fixtures / "ads" / name).read_text(), FakeEmbedder())
    assert len(parsed.passages) == len(gold)
    for p, (prefix, _) in zip(parsed.passages, gold, strict=True):
        assert p.text.startswith(prefix)
