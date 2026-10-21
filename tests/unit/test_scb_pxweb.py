import datetime as dt

from lonekrav.etl import scb_pxweb

T = dt.datetime(2026, 10, 20, tzinfo=dt.UTC)


def rows(fixtures, table):
    return {(r.code, r.year): r for r in
            scb_pxweb.parse_distributions(fixtures / f"pxweb/{table}.json", table, T)}


def test_tab5932_values_and_cis(fixtures):
    r = rows(fixtures, "TAB5932")
    assert r[("0000", 2025)].median == 38300
    s = r[("2512", 2025)]
    assert (s.mean, s.median, s.p10, s.p25, s.p75, s.p90) == (55500, 53500, 39600, 46200, 62600,
                                                              72600)
    assert (s.mean_ci95, s.median_ci95, s.p10_ci95, s.p90_ci95) == (940, 880, 1080, 1340)
    assert s.source_table == "TAB5932" and s.reference_year == 2025 and s.fetched_at == T


def test_tab4265_has_no_cis(fixtures):
    s = rows(fixtures, "TAB4265")[("2512", 2014)]
    assert (s.mean, s.median, s.p10, s.p90) == (41200, 40000, 28100, 55000)
    assert s.mean_ci95 is None and s.p10_ci95 is None


def test_suppressed_cells_stay_null(fixtures):
    r = rows(fixtures, "TAB4265")
    suppressed = [x for x in r.values() if x.suppressed]
    assert suppressed, "fixture has suppressed cells (status '..')"
    assert all(getattr(x, f) is None for x in suppressed for f in x.suppressed)


def test_occupation_labels_exclude_aggregates(fixtures):
    labels = scb_pxweb.occupation_labels(fixtures / "pxweb/TAB5932.json")
    assert labels["0110"] == "Officerare"
    assert "0000" not in labels
