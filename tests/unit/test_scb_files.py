from lonekrav.etl import scb_files


def test_structure(fixtures):
    titles = scb_files.parse_structure(fixtures / "scb/ssyk-2012-koder.xlsx")
    assert titles["2512"] == "Mjukvaru- och systemutvecklare m.fl."  # leading space stripped
    assert titles["1212"] == "Ekonomi- och finanschefer, nivå 2"
    assert all(len(c) == 4 and c.isdigit() for c in titles)


def test_english(fixtures):
    titles = scb_files.parse_english(fixtures / "scb/structur_english_ssyk2012_1_4.xlsx")
    assert titles["2512"] == "Software- and system developers"
    assert "Name" not in titles.values()


def test_isco_key_splits_and_pads(fixtures):
    key = scb_files.parse_isco_key(fixtures / "scb/webb_nyckel_ssyk2012_isco-08_20160905.xlsx")
    assert key["2512"] == ["2511", "2512", "2513", "2514", "2521"]
    assert key["0110"] == ["0110"]
    assert key["1212"] == ["1211"]


def test_title_index_pads_military_codes(fixtures):
    idx = scb_files.parse_title_index(fixtures / "scb/ssyk_index_webb_2026.xlsx")
    assert "Arméofficer" in idx["0110"]
    assert "Systemutvecklare" in idx["2512"]
    assert len(idx["2512"]) >= 20


def test_major_groups_in_swedish_and_english(fixtures):  # 007: the map's group labels
    from lonekrav.etl.scb_files import parse_major_groups

    g = parse_major_groups(fixtures / "scb/ssyk-2012-koder.xlsx",
                           fixtures / "scb/structur_english_ssyk2012_1_4.xlsx")
    assert sorted(g) == ["0", "1"]  # the fixture slices hold only these in both languages
    assert g["1"] == {"sv": "Chefsyrken", "en": "Managers"}
    assert g["0"]["en"] == "Armed forces occupations"
