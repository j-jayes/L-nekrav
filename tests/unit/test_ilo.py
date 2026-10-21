from lonekrav.etl import ilo


def test_unit_group(fixtures):
    groups = ilo.parse(fixtures / "ilo/isco08_en.xlsx")
    g = groups["2512"]
    assert g.title == "Software Developers"
    assert g.definition == "Synthetic definition of ISCO-08 2512 (not ILO text)."
    assert g.tasks.startswith("(a)")
    assert g.included == ["Synthetic example A of 2512", "Synthetic example B of 2512"]


def test_only_unit_groups(fixtures):
    groups = ilo.parse(fixtures / "ilo/isco08_en.xlsx")
    assert all(len(c) == 4 for c in groups)
    assert "1" not in groups


def test_fixture_holds_no_ilo_text(fixtures):
    """ILO reserves reproduction rights; the fixture keeps only codes and titles (PR #1 review)."""
    for g in ilo.parse(fixtures / "ilo/isco08_en.xlsx").values():
        assert g.definition.startswith("Synthetic") and "synthetic" in g.tasks
