from lonekrav.core.profiles import build_profiles, discrepancies, write_profiles
from lonekrav.etl import jobtech

FIXTURE_CODES = {"0110", "1211", "1212", "2421", "2512", "3511", "4430", "5322", "5343", "9210"}


def test_one_profile_per_salary_table_code(inputs):
    profiles = build_profiles(inputs)
    assert set(profiles) == FIXTURE_CODES  # 0000 is the national row, not an occupation


def test_military_code_titles_from_salary_table_and_ilo(inputs):
    p = build_profiles(inputs)["0110"]
    assert p.title_sv == "Officerare"
    assert p.title_en == "Commissioned Armed Forces Officers"


def test_2512_profile(inputs):
    p = build_profiles(inputs)["2512"]
    assert p.legal_flags == []
    assert p.isco_codes == ["2511", "2512", "2513", "2514", "2521"]
    assert {d.lang for d in p.descriptions} == {"sv", "en"}
    sv = [s.label for s in p.synonyms if s.lang == "sv"]
    en = [s.label for s in p.synonyms if s.lang == "en"]
    assert len(sv) >= 20 and "Backend-utvecklare" in sv
    assert en
    assert len({(s.lang, s.label.casefold()) for s in p.synonyms}) == len(p.synonyms)
    assert all(s.match_type != "broad" for s in p.synonyms)


def test_merged_manager_code_uses_mis_text_and_shared_jobtech_text(inputs):
    p = build_profiles(inputs)["1212"]
    assert p.jobtech_shared
    sv = [d for d in p.descriptions if d.lang == "sv"]
    assert sv[0].source.source == "scb_mis2012"
    assert sv[0].text.startswith("Verksamhetsnära chef")
    assert any(d.source.source == "jobtech" and d.shared_with == ["1211", "1212"] for d in sv)


def test_code_missing_from_jobtech_uses_mis(inputs):
    p = build_profiles(inputs)["5322"]
    assert p.jobtech_concept_id is None
    assert p.descriptions[0].source.source == "scb_mis2012"


def test_missing_ilo_text_still_builds_and_records_absence(inputs):
    for isco in inputs.isco_key["5322"]:
        inputs.ilo.pop(isco, None)
    p = build_profiles(inputs)["5322"]
    assert all(s.source != "ilo_isco08" for s in p.sources)
    assert p.title_en  # SCB English title still present


def test_legal_flags_attached(inputs):
    profiles = build_profiles(inputs)
    assert [f.kind for f in profiles["3511"].legal_flags] == ["exempt_75"]
    assert [f.kind for f in profiles["5343"].legal_flags] == ["banned"]


def test_discrepancies(inputs, tmp_path):
    rows = {r["code"]: r for r in discrepancies(inputs)}
    assert rows["0110"]["in_structure"] is False and rows["0110"]["in_salary_table"] is True
    assert rows["1212"]["in_jobtech"] is False and rows["1212"]["jobtech_code"] == "1210"
    assert rows["5322"]["jobtech_code"] == ""


def test_output_is_sorted_and_deterministic(inputs, tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    write_profiles(build_profiles(inputs), a)
    write_profiles(build_profiles(inputs), b)
    assert a.read_bytes() == b.read_bytes()
    text = a.read_text()
    assert text.index('"code": "0110"') < text.index('"code": "9210"')
    assert "Mjukvaru- och systemutvecklare" in text  # not ASCII-escaped


def test_esco_occupation_reached_only_by_broad_match_is_not_used(inputs):
    uri = "http://data.europa.eu/esco/occupation/60082a99-d8ef-4e84-9290-78902681b6ed"
    assert uri in inputs.esco  # "företagsanalytiker", close-matched under 2421 only
    g = inputs.jobtech_by_scb["2512"]
    first = g.names[0]
    broad = jobtech.EscoMatch(uri=uri, label="företagsanalytiker", match_type="broad")
    names = [first.model_copy(update={"esco": [broad]}), *g.names[1:]]
    inputs.jobtech_by_scb["2512"] = g.model_copy(update={"names": names})
    p = build_profiles(inputs)["2512"]
    assert all(s.esco_uri != uri for s in p.synonyms)
    assert all(src.ref != uri for src in p.sources)
