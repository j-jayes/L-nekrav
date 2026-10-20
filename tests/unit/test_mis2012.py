import json

from lonekrav.etl import mis2012


def pages(fixtures):
    return {int(k): v for k, v in json.loads((fixtures / "mis2012/pages.json").read_text()).items()}


def test_descriptions_come_from_description_section(fixtures):
    d = mis2012.parse(pages(fixtures))
    assert d["1212"].startswith("Verksamhetsnära chef underställd mellanchef")
    assert "Hit hör inte:" in d["1212"]
    assert d["5322"].startswith("Ger stöd, assistans, omvårdnad och social service")
    assert d["4430"]


def test_hyphenation_joined_and_entries_bounded(fixtures):
    d = mis2012.parse(pages(fixtures))
    assert "motsvarande" in d["1211"] and "motsvar-" not in d["1211"]
    assert "Yrkesgrupp" not in d["1212"]
    assert "5323" not in d["5322"]


def test_overview_and_appendix_pages_ignored(fixtures):
    p = pages(fixtures)
    only_other = {k: v for k, v in p.items() if "Yrkesområde" not in v.splitlines()[0]}
    assert mis2012.parse(only_other) == {}


def test_entry_does_not_continue_across_missing_pages(fixtures):
    d = mis2012.parse(pages(fixtures))  # fixture holds pages 76 and 81 but not 77-80
    assert "tryck, tar prover" not in d["4430"]
    assert d["4430"].endswith("(1113)")
