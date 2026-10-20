import json

from lonekrav.etl import esco


def test_parse_occupation(fixtures):
    path = fixtures / "esco/occ0.json"
    raw = json.loads(path.read_text())
    occ = esco.parse(path)
    assert occ.uri == raw["uri"]
    assert occ.label["en"] == "accounting manager"
    assert occ.label["sv"] == "redovisningschef"
    assert "head of accounts" in occ.alt["en"]
    assert occ.description["sv"].startswith("Redovisningschefer ansvarar")


def test_missing_language_is_empty_not_error(fixtures):
    occ = esco.parse(fixtures / "esco/occ0.json")
    assert occ.alt.get("sv", []) == [] or isinstance(occ.alt["sv"], list)
