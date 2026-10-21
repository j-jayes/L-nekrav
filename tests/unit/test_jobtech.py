from lonekrav.etl import jobtech


def test_parse_groups(fixtures):
    groups = jobtech.parse(fixtures / "jobtech/ssyk_level_4.json")
    g = groups["2512"]
    assert g.concept_id == "DJh5_yyF_hEM"
    assert g.definition.startswith("Analyserar, designar och utvecklar IT-system")
    names = {n.label: n for n in g.names}
    assert "Backend-utvecklare" in names
    assert all(m.match_type in {"exact", "close", "broad", "narrow"} for n in g.names for m in n.esco)


def test_alternative_labels_kept(fixtures):
    groups = jobtech.parse(fixtures / "jobtech/ssyk_level_4.json")
    alts = [a for n in groups["3511"].names for a in n.alt_labels]
    assert isinstance(alts, list)


def test_merged_manager_code_expands_to_both_levels(fixtures):
    groups = jobtech.parse(fixtures / "jobtech/ssyk_level_4.json")
    by_scb = jobtech.expand_merged(groups, scb_codes={"1211", "1212", "2512", "4430"})
    assert by_scb["1211"].concept_id == by_scb["1212"].concept_id == groups["1210"].concept_id
    assert by_scb["1211"].shared_with == ["1211", "1212"]
    assert by_scb["2512"].shared_with == []
    assert "4430" not in by_scb
    assert "1210" not in by_scb
