"""Official SCB salary statistics: Parquet storage and loading. Nothing is imputed."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Literal

import polars as pl
from pydantic import BaseModel

from lonekrav.core.models import AgeBandSalary, SalaryDistribution

DISTRIBUTIONS = Path("data/processed/salary_distributions.parquet")
AGE_BANDS = Path("data/processed/salary_age.parquet")


def _write(rows: list, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [r.model_dump(exclude={"suppressed"}) for r in rows]
    pl.DataFrame(data, infer_schema_length=None).write_parquet(path, statistics=False)


def write_distributions(rows: list[SalaryDistribution], path: Path = DISTRIBUTIONS) -> None:
    _write(sorted(rows, key=lambda d: (d.code, d.year)), path)


def write_age_bands(rows: list[AgeBandSalary], path: Path = AGE_BANDS) -> None:
    _write(sorted(rows, key=lambda a: (a.code, a.year, a.age_band)), path)


def load_distributions(path: Path = DISTRIBUTIONS) -> list[SalaryDistribution]:
    return [SalaryDistribution.model_validate(r) for r in pl.read_parquet(path).to_dicts()]


def load_age_bands(path: Path = AGE_BANDS) -> list[AgeBandSalary]:
    return [AgeBandSalary.model_validate(r) for r in pl.read_parquet(path).to_dicts()]


# --- the salary payload for one occupation (Feature 002, spec FR-024–FR-026) ----------------

AGE_BANDS_ = ("18-24", "25-34", "35-44", "45-54", "55-64", "65-68")
FORMULA = "percentile × age_band_mean ÷ all_ages_mean"
PERCENTILES = ("p10", "p25", "median", "p75", "p90")


class ThresholdLine(BaseModel):
    rule_id: str
    percent: float
    amount_sek: int
    median_sek: int
    median_reference_year: int
    on: dt.date


class TableRef(BaseModel):
    table: str
    reference_year: int


class SimulatedPercentiles(BaseModel):
    """Not an SCB figure: SCB publishes percentiles for all ages and means per age band, so this
    scales each percentile by the band's mean relative to the all-ages mean."""
    age_band: str
    year: int
    p10: int | None
    p25: int | None
    median: int | None
    p75: int | None
    p90: int | None
    is_simulated: Literal[True] = True
    formula: str = FORMULA
    inputs: list[TableRef]


class SalaryPayload(BaseModel):
    code: str
    title_sv: str
    title_en: str
    distributions: list[SalaryDistribution]
    age_bands: list[AgeBandSalary]
    thresholds: list[ThresholdLine]
    applicable_rule_id: str | None
    simulated: SimulatedPercentiles | None = None
    no_occupation_data: bool


def _simulate(d: SalaryDistribution, age_band: str, band: AgeBandSalary | None,
              every: AgeBandSalary | None) -> SimulatedPercentiles:
    """Null in, null out: a missing percentile or mean gives a missing simulated value."""
    factor = (band.mean_monthly / every.mean_monthly
              if band and every and band.mean_monthly and every.mean_monthly else None)
    values = {p: round(getattr(d, p) * factor) if factor and getattr(d, p) is not None else None
              for p in PERCENTILES}
    inputs = [TableRef(table=d.source_table, reference_year=d.reference_year)]
    if band:
        inputs.append(TableRef(table=band.source_table, reference_year=band.reference_year))
    return SimulatedPercentiles(age_band=age_band, year=d.year, inputs=inputs, **values)


def payload(code: str, on: dt.date, age_band: str | None = None,
            distributions: list[SalaryDistribution] | None = None,
            age_bands: list[AgeBandSalary] | None = None,
            titles: dict[str, tuple[str, str]] | None = None) -> SalaryPayload:
    from lonekrav.core.legal import load_registry

    if age_band is not None and age_band not in AGE_BANDS_:
        raise ValueError(f"age_band must be one of {list(AGE_BANDS_)}, not {age_band!r}")
    dists = sorted((d for d in (distributions if distributions is not None
                                else load_distributions()) if d.code == code),
                   key=lambda d: d.year)
    ages_all = [a for a in (age_bands if age_bands is not None else load_age_bands())
                if a.code == code]
    latest = max((a.year for a in ages_all), default=None)
    ages = [a for a in ages_all if a.year == latest]

    reg = load_registry()
    median = reg.median_on(on)
    lines = [] if median is None else [
        ThresholdLine(rule_id=r, percent=float(reg.rules[r].percent),
                      amount_sek=reg.threshold(r, median), median_sek=median.amount,
                      median_reference_year=median.scb_reference_year, on=on)
        for r in ("salary_90", "salary_75_exempt")]
    if code in reg.codes_on("banned", on):
        applicable = None
    elif code in reg.codes_on("exempt_75", on):
        applicable = "salary_75_exempt"
    else:
        applicable = "salary_90"

    simulated = None
    if age_band and dists:
        d = dists[-1]
        pick = {a.age_band: a for a in ages_all if a.year == d.year}
        simulated = _simulate(d, age_band, pick.get(age_band), pick.get("all"))
    sv, en = (titles or {}).get(code, ("", ""))
    return SalaryPayload(code=code, title_sv=sv, title_en=en, distributions=dists, age_bands=ages,
                         thresholds=lines, applicable_rule_id=applicable, simulated=simulated,
                         no_occupation_data=not dists)
