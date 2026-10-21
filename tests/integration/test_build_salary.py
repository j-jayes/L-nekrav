import datetime as dt
import json
import shutil

import polars as pl
import pytest

from lonekrav.core import salary
from lonekrav.etl import scb_pxweb

T = dt.datetime(2026, 10, 20, 12, tzinfo=dt.UTC)


def cell(j, **coords) -> int:
    """Flat json-stat2 value index for the given category codes (row-major over j['id'])."""
    idx = 0
    for dim, size in zip(j["id"], j["size"], strict=True):
        pos = j["dimension"][dim]["category"]["index"]  # code -> position
        idx = idx * size + (pos[coords[dim]] if dim in coords else 0)
    return idx


@pytest.fixture
def raw(fixtures, tmp_path):
    """Fixture tables laid out as a fetched data/raw/pxweb/, with .meta.json beside each."""
    d = tmp_path / "raw" / "pxweb"
    d.mkdir(parents=True)
    for t in scb_pxweb.TABLES:
        shutil.copy(fixtures / f"pxweb/{t}.json", d / f"{t}.json")
        (d / f"{t}.json.meta.json").write_text(json.dumps(
            {"url": "u", "fetched_at": T.isoformat(), "sha256": "x"}))
    return tmp_path / "raw"


def test_each_code_year_once_from_the_right_table(raw):
    dists = scb_pxweb.build_distributions(raw)
    keys = [(d.code, d.year) for d in dists]
    assert len(keys) == len(set(keys))
    assert {d.source_table for d in dists if d.year <= 2022} == {"TAB4265"}
    assert {d.source_table for d in dists if d.year >= 2023} == {"TAB5932"}
    assert min(d.year for d in dists) == 2014 and max(d.year for d in dists) == 2025
    assert all(d.fetched_at == T for d in dists)


def test_age_bands_from_the_right_table(raw):
    ages = scb_pxweb.build_age_bands(raw)
    assert {a.source_table for a in ages if a.year <= 2022} == {"TAB4264"}
    assert {a.source_table for a in ages if a.year >= 2023} == {"TAB5844"}


def test_parquet_roundtrip_keeps_nulls(raw, tmp_path):
    dists = scb_pxweb.build_distributions(raw)
    out = tmp_path / "d.parquet"
    salary.write_distributions(dists, out)
    df = pl.read_parquet(out)
    assert df.height == len(dists)
    assert df.filter(pl.col("p10").is_null()).height == sum(d.p10 is None for d in dists)
    assert salary.load_distributions(out) == sorted(dists, key=lambda d: (d.code, d.year))


def test_unordered_percentiles_fail_the_build_naming_code_and_year(raw):
    p = raw / "pxweb" / "TAB5932.json"
    j = json.loads(p.read_text())
    j["value"][cell(j, Yrke2012="2512", Tid="2025", ContentsCode="000007CF")] = 99999  # P10 > P25
    p.write_text(json.dumps(j))
    with pytest.raises(ValueError, match="2512 2025"):
        scb_pxweb.build_distributions(raw)
