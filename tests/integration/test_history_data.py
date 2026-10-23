"""The committed yearly ad counts cover every JobTech concept and every full year (SC-005)."""

from collections import Counter

from lonekrav.core.market import load_history
from lonekrav.core.profiles import load_profiles


def test_one_count_per_concept_per_year_from_2016():
    rows = load_history()
    years = sorted({r.year for r in rows})
    assert years[0] == 2016 and years == list(range(2016, years[-1] + 1))
    concepts = {p.jobtech_concept_id for p in load_profiles().values() if p.jobtech_concept_id}
    per_concept = Counter(r.concept_id for r in rows)
    assert set(per_concept) == concepts
    assert set(per_concept.values()) == {len(years)}


def test_2512_matches_the_probe():
    by_year = {r.year: r.ads for r in load_history() if r.concept_id == "DJh5_yyF_hEM"}
    assert by_year[2016] == 16406 and by_year[2025] == 30304  # research R4, 2026-10-23
