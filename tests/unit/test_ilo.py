from lonekrav.etl import ilo


def test_unit_group(fixtures):
    groups = ilo.parse(fixtures / "ilo/isco08_en.xlsx")
    g = groups["2512"]
    assert g.title == "Software Developers"
    assert g.definition.startswith("Software developers research, analyse and evaluate")
    assert g.tasks.startswith("(a)")
    assert "Software engineer" in g.included
    assert "Programmer analyst" in g.included


def test_only_unit_groups(fixtures):
    groups = ilo.parse(fixtures / "ilo/isco08_en.xlsx")
    assert all(len(c) == 4 for c in groups)
    assert "1" not in groups
