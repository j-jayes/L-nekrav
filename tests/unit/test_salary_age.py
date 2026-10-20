import datetime as dt

from lonekrav.etl import scb_pxweb

T = dt.datetime(2026, 10, 20, tzinfo=dt.UTC)


def rows(fixtures, table):
    return {(r.code, r.year, r.age_band): r for r in
            scb_pxweb.parse_age_bands(fixtures / f"pxweb/{table}.json", table, T)}


def test_tab5844_suppressed_headcount(fixtures):
    r = rows(fixtures, "TAB5844")
    young = r[("2512", 2025, "18-24")]
    assert young.mean_monthly == 36100 and young.mean_ci95 == 1800
    assert young.headcount is None and young.suppressed == ["headcount"]
    assert r[("2512", 2025, "all")].headcount == 113100


def test_band_65_66_dropped_and_all_ages_kept(fixtures):
    bands = {k[2] for k in rows(fixtures, "TAB5844")}
    assert bands == {"18-24", "25-34", "35-44", "45-54", "55-64", "65-68", "all"}


def test_tab4264_source(fixtures):
    r = rows(fixtures, "TAB4264")[("2512", 2014, "25-34")]
    assert (r.mean_monthly, r.headcount, r.mean_ci95) == (34700, 19400, None)
    assert r.source_table == "TAB4264"
