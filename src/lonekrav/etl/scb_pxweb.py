"""SCB PxWeb v2 salary tables (json-stat2), all sectors and both sexes combined.

| Years     | Percentiles + mean | Age bands |
|-----------|--------------------|-----------|
| 2014-2022 | TAB4265 (no CIs)   | TAB4264   |
| 2023-     | TAB5932            | TAB5844   |

Regional means (Feature 005): TAB5696, by national area, 2023 on, fetched in English for the
area names. Not TAB4185, which is pay within the regions as employers (research R3).
"""

from __future__ import annotations

import datetime as dt
import itertools
import json
from collections.abc import Iterator
from pathlib import Path

from lonekrav.core.models import AgeBandSalary, RegionalSalary, SalaryDistribution
from lonekrav.etl.http import cached_get, read_meta

URL = "https://statistikdatabasen.scb.se/api/v2/tables/{table}/data"
DISTRIBUTION_TABLES = ("TAB4265", "TAB5932")
AGE_TABLES = ("TAB4264", "TAB5844")
TABLES = DISTRIBUTION_TABLES + AGE_TABLES
REGIONAL_TABLE = "TAB5696"
REGIONAL_FIELD = {"000007AS": "mean", "000007AU": "mean_ci95", "000007AP": "employees"}
NOT_OCCUPATIONS = {"0001", "0002"}  # "other" and "unknown"; 0000 (all occupations) is kept
FIELD = {  # content label -> model field
    "Månadslön": "mean",
    "Medianlön": "median",
    "10:e percentilen": "p10",
    "25:e percentilen": "p25",
    "75:e percentilen": "p75",
    "90:e percentilen": "p90",
    "Månadslön, 95 procent konfidensintervall": "mean_ci95",
    "Medianlön, 95 procent konfidensintervall": "median_ci95",
    "Månadslön, 10:e percentilen, 95 procent konfidensintervall": "p10_ci95",
    "Månadslön, 25:e percentilen, 95 procent konfidensintervall": "p25_ci95",
    "Månadslön, 75:e percentilen, 95 procent konfidensintervall": "p75_ci95",
    "Månadslön, 90:e percentilen, 95 procent konfidensintervall": "p90_ci95",
}
AGE_FIELD = {
    "Månadslön": "mean_monthly",
    "Antal anställda": "headcount",
    "Månadslön, 95 procent konfidensintervall": "mean_ci95",
}
AGE_BAND = {"18-24": "18-24", "25-34": "25-34", "35-44": "35-44", "45-54": "45-54",
            "55-64": "55-64", "65-68": "65-68", "tot": "all"}  # 65-66 was replaced by 65-68


def _validate(data: bytes) -> None:
    j = json.loads(data)
    if "value" not in j or "dimension" not in j:
        raise ValueError(f"not json-stat2: {str(j)[:200]}")


def fetch(raw: Path, force: bool = False) -> dict[str, Path]:
    out = {}
    for t in TABLES:
        params = {
            "lang": "sv", "outputFormat": "json-stat2",
            "valueCodes[Sektor]": "0", "valueCodes[Kon]": "1+2", "valueCodes[Yrke2012]": "*",
            "valueCodes[Tid]": "*", "valueCodes[ContentsCode]": "*",
        }
        if t in AGE_TABLES:
            params["valueCodes[Alder]"] = "*"
        out[t] = cached_get("scb_pxweb", URL.format(table=t), raw / "pxweb" / f"{t}.json",
                            params=params, force=force, validate=_validate)
    params = {"lang": "en", "outputFormat": "json-stat2", "valueCodes[Region]": "*",
              "valueCodes[Sektor]": "0", "valueCodes[Kon]": "1+2", "valueCodes[Yrke2012]": "*",
              "valueCodes[Tid]": "*", "valueCodes[ContentsCode]": ",".join(REGIONAL_FIELD)}
    out[REGIONAL_TABLE] = cached_get(
        "scb_pxweb", URL.format(table=REGIONAL_TABLE), raw / "pxweb" / f"{REGIONAL_TABLE}.json",
        params=params, force=force, validate=_validate)
    return out


def _cells(path: Path) -> Iterator[dict[str, str | int | None]]:
    """Yield one dict per cell: dimension -> category code, plus 'label' and 'value'."""
    j = json.loads(path.read_text())
    dims = j["id"]
    cats = {}
    for d in dims:
        pos = j["dimension"][d]["category"]["index"]
        cats[d] = sorted(pos, key=pos.get)
    labels = j["dimension"]["ContentsCode"]["category"]["label"]
    for i, combo in enumerate(itertools.product(*(cats[d] for d in dims))):
        cell = dict(zip(dims, combo, strict=True))
        cell["label"] = labels[cell["ContentsCode"]]
        cell["value"] = j["value"][i]  # null when SCB suppresses the cell (status "..")
        yield cell


def occupation_labels(path: Path) -> dict[str, str]:
    """Swedish label per occupation code (excluding 0000, 0001, 0002)."""
    labels = json.loads(path.read_text())["dimension"]["Yrke2012"]["category"]["label"]
    return {c: lab.strip() for c, lab in labels.items() if c not in NOT_OCCUPATIONS | {"0000"}}


def parse_distributions(path: Path, table: str, fetched_at: dt.datetime) -> list[SalaryDistribution]:
    grouped: dict[tuple[str, int], dict] = {}
    for c in _cells(path):
        if c["Yrke2012"] in NOT_OCCUPATIONS or c["label"] not in FIELD:
            continue
        key = (c["Yrke2012"], int(c["Tid"]))
        grouped.setdefault(key, {})[FIELD[c["label"]]] = c["value"]
    return [SalaryDistribution(code=code, year=year, source_table=table, reference_year=year,
                               fetched_at=fetched_at, **{f: v.get(f) for f in
                                                         ("mean", "median", "p10", "p25", "p75",
                                                          "p90")},
                               **{k: x for k, x in v.items() if k.endswith("_ci95")})
            for (code, year), v in sorted(grouped.items())]


def parse_age_bands(path: Path, table: str, fetched_at: dt.datetime) -> list[AgeBandSalary]:
    grouped: dict[tuple[str, int, str], dict] = {}
    for c in _cells(path):
        if (c["Yrke2012"] in NOT_OCCUPATIONS or c["label"] not in AGE_FIELD
                or c["Alder"] not in AGE_BAND):
            continue
        key = (c["Yrke2012"], int(c["Tid"]), AGE_BAND[c["Alder"]])
        grouped.setdefault(key, {})[AGE_FIELD[c["label"]]] = c["value"]
    return [AgeBandSalary(code=code, year=year, age_band=band, source_table=table,
                          reference_year=year, fetched_at=fetched_at,
                          mean_monthly=v.get("mean_monthly"), headcount=v.get("headcount"),
                          mean_ci95=v.get("mean_ci95"))
            for (code, year, band), v in sorted(grouped.items())]


def parse_regional(path: Path, fetched_at: dt.datetime) -> list[RegionalSalary]:
    names = json.loads(path.read_text())["dimension"]["Region"]["category"]["label"]
    grouped: dict[tuple[str, int, str], dict] = {}
    for c in _cells(path):
        if c["Yrke2012"] in NOT_OCCUPATIONS or c["ContentsCode"] not in REGIONAL_FIELD:
            continue
        key = (c["Yrke2012"], int(c["Tid"]), c["Region"])
        grouped.setdefault(key, {})[REGIONAL_FIELD[c["ContentsCode"]]] = c["value"]
    return [RegionalSalary(code=code, year=year, region=region, region_name=names[region],
                           source_table=REGIONAL_TABLE, reference_year=year,
                           fetched_at=fetched_at, mean=v.get("mean"),
                           mean_ci95=v.get("mean_ci95"), employees=v.get("employees"))
            for (code, year, region), v in sorted(grouped.items())]


def build_regional(raw: Path) -> list[RegionalSalary]:
    p = raw / "pxweb" / f"{REGIONAL_TABLE}.json"
    return parse_regional(p, read_meta(p).fetched_at)


def build_distributions(raw: Path) -> list[SalaryDistribution]:
    """Both tables, each year from exactly one table (the newer table wins on overlap)."""
    rows: dict[tuple[str, int], SalaryDistribution] = {}
    for t in DISTRIBUTION_TABLES:
        p = raw / "pxweb" / f"{t}.json"
        for r in parse_distributions(p, t, read_meta(p).fetched_at):
            rows[(r.code, r.year)] = r
    return [rows[k] for k in sorted(rows)]


def build_age_bands(raw: Path) -> list[AgeBandSalary]:
    rows: dict[tuple[str, int, str], AgeBandSalary] = {}
    for t in AGE_TABLES:
        p = raw / "pxweb" / f"{t}.json"
        for r in parse_age_bands(p, t, read_meta(p).fetched_at):
            rows[(r.code, r.year, r.age_band)] = r
    return [rows[k] for k in sorted(rows)]
