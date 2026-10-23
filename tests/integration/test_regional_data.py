"""The committed regional table agrees with the national salary table (research R3 cross-check).

TAB5696's Sweden row and TAB5932 publish the same mean monthly salary for a code and year; a
mismatch means the wrong table or content code was fetched.
"""

from lonekrav.core.salary import load_distributions, load_regional


def test_sweden_row_equals_the_national_mean():
    national = {(d.code, d.year): d.mean for d in load_distributions()}
    pairs = [(r.mean, national[(r.code, r.year)]) for r in load_regional()
             if r.region == "SE" and (r.code, r.year) in national]
    assert len(pairs) > 1000
    assert [p for p in pairs if p[0] != p[1]] == []


def test_every_area_for_the_latest_year():
    rows = load_regional()
    latest = max(r.year for r in rows)
    assert latest >= 2025
    assert len({r.region for r in rows if r.year == latest}) == 9
