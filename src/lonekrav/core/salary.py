"""Official SCB salary statistics: Parquet storage and loading. Nothing is imputed."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Literal

import polars as pl
from pydantic import BaseModel

from lonekrav.core.legal import Source
from lonekrav.core.models import AgeBandSalary, RegionalSalary, SalaryDistribution

DISTRIBUTIONS = Path("data/processed/salary_distributions.parquet")
AGE_BANDS = Path("data/processed/salary_age.parquet")
REGIONAL = Path("data/processed/salary_regional.parquet")


def _write(rows: list, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [r.model_dump(exclude={"suppressed"}) for r in rows]
    pl.DataFrame(data, infer_schema_length=None).write_parquet(path, statistics=False)


def write_distributions(rows: list[SalaryDistribution], path: Path = DISTRIBUTIONS) -> None:
    _write(sorted(rows, key=lambda d: (d.code, d.year)), path)


def write_age_bands(rows: list[AgeBandSalary], path: Path = AGE_BANDS) -> None:
    _write(sorted(rows, key=lambda a: (a.code, a.year, a.age_band)), path)


def write_regional(rows: list[RegionalSalary], path: Path = REGIONAL) -> None:
    _write(sorted(rows, key=lambda r: (r.code, r.year, r.region)), path)


def load_distributions(path: Path = DISTRIBUTIONS) -> list[SalaryDistribution]:
    return [SalaryDistribution.model_validate(r) for r in pl.read_parquet(path).to_dicts()]


def load_age_bands(path: Path = AGE_BANDS) -> list[AgeBandSalary]:
    return [AgeBandSalary.model_validate(r) for r in pl.read_parquet(path).to_dicts()]


def load_regional(path: Path = REGIONAL) -> list[RegionalSalary]:
    return [RegionalSalary.model_validate(r) for r in pl.read_parquet(path).to_dicts()]


# --- the salary payload for one occupation (Feature 002, spec FR-024–FR-026) ----------------

AGE_BANDS_ = ("18-24", "25-34", "35-44", "45-54", "55-64", "65-68")
FORMULA = "percentile × age_band_mean ÷ all_ages_mean"
REGION_FORMULA = "percentile × area_mean ÷ sweden_mean"
BOTH_FORMULA = ("percentile × age_band_mean ÷ all_ages_mean × area_mean ÷ sweden_mean "
                "(the two factors are assumed independent)")
# SCB's eight national areas (riksområden) in TAB5696; "SE" is Sweden, the reference
REGIONS = ("SE11", "SE12", "SE21", "SE22", "SE23", "SE31", "SE32", "SE33")
PERCENTILES = ("p10", "p25", "median", "p75", "p90")
LINE_RULES = ("maintenance_80", "salary_90", "salary_75_exempt")


class ThresholdLine(BaseModel):
    rule_id: str
    percent: float
    amount_sek: int
    median_sek: int
    median_reference_year: int
    on: dt.date
    source: Source  # the rule's legal source, so every surface can cite the line (FR-006)


class TableRef(BaseModel):
    table: str
    reference_year: int


class LeftOut(BaseModel):
    factor: Literal["age", "region"]
    reason: str


class SimulatedPercentiles(BaseModel):
    """Not an SCB figure: SCB publishes percentiles only for all ages in all of Sweden, and means
    per age band and per national area, so this scales each percentile by the band's mean relative
    to the all-ages mean and the area's mean relative to Sweden's. A factor whose inputs SCB does
    not publish is left out, with the reason (006 FR-008–FR-010)."""
    age_band: str | None = None
    region: str | None = None
    year: int
    p10: int | None
    p25: int | None
    median: int | None
    p75: int | None
    p90: int | None
    is_simulated: Literal[True] = True
    formula: str = FORMULA
    inputs: list[TableRef]
    applied: list[Literal["age", "region"]]
    left_out: list[LeftOut] = []


Percentile = Literal["p10", "p25", "median", "p75", "p90"]


class PercentileRef(BaseModel):
    name: Percentile
    value_sek: int


class MarketPosition(BaseModel):
    """Where an amount sits among SCB's published percentiles: the nearest published one below
    and above (either may be open), or the one it equals. Values are copied, never interpolated."""
    amount_sek: int
    year: int
    source_table: str
    lower: PercentileRef | None = None
    upper: PercentileRef | None = None
    at: PercentileRef | None = None
    missing: list[Percentile] = []  # suppressed percentiles between lower and upper
    no_data: bool = False


def position(amount: int, d: SalaryDistribution) -> MarketPosition:
    out = MarketPosition(amount_sek=amount, year=d.year, source_table=d.source_table)
    published = [PercentileRef(name=n, value_sek=getattr(d, n)) for n in PERCENTILES
                 if getattr(d, n) is not None]
    if not published:
        return out.model_copy(update={"no_data": True})
    if at := next((r for r in published if r.value_sek == amount), None):
        return out.model_copy(update={"at": at})
    lower = next((r for r in reversed(published) if r.value_sek < amount), None)
    upper = next((r for r in published if r.value_sek > amount), None)
    lo = PERCENTILES.index(lower.name) + 1 if lower else 0
    hi = PERCENTILES.index(upper.name) if upper else len(PERCENTILES)
    missing = [n for n in PERCENTILES[lo:hi] if getattr(d, n) is None]
    return out.model_copy(update={"lower": lower, "upper": upper, "missing": missing})


class SalaryPayload(BaseModel):
    code: str
    title_sv: str
    title_en: str
    distributions: list[SalaryDistribution]
    age_bands: list[AgeBandSalary]
    thresholds: list[ThresholdLine]
    applicable_rule_id: str | None
    simulated: SimulatedPercentiles | None = None
    estimate_note: str | None = None  # why no estimate was made, when one was asked for
    no_occupation_data: bool


def _ratio(rows: dict, num: str, den: str, table: str, year: int,
           label: dict[str, str]) -> tuple[float | None, str | None]:
    """num's mean ÷ den's mean, or the reason SCB's figures do not allow it."""
    if not rows:
        return None, f"no {table} figures for {year}"
    for key in (num, den):
        if rows.get(key) is None:
            return None, f"SCB publishes no mean for {label.get(key, key)} in {year} ({table})"
    return rows[num] / rows[den], None


def _simulate(d: SalaryDistribution, age_band: str | None, ages: list[AgeBandSalary],
              region: str | None, areas: list[RegionalSalary]
              ) -> tuple[SimulatedPercentiles | None, str | None]:
    """Null in, null out: a missing percentile gives a missing simulated value."""
    if d.p25 is None and d.p75 is None:
        return None, f"SCB publishes neither P25 nor P75 for {d.code} in {d.year}"
    factor, applied, left, inputs = 1.0, [], [], [TableRef(table=d.source_table,
                                                           reference_year=d.year)]
    if age_band:
        rows = {a.age_band: a.mean_monthly for a in ages if a.year == d.year}
        f, why = _ratio(rows, age_band, "all", "TAB5844", d.year,
                        {age_band: f"ages {age_band}", "all": "all ages"})
        if f is None:
            left.append(LeftOut(factor="age", reason=why))
        else:
            factor, applied = factor * f, [*applied, "age"]
            inputs.append(TableRef(table="TAB5844", reference_year=d.year))
    if region:
        rows = {r.region: r.mean for r in areas if r.year == d.year}
        names = {r.region: r.region_name for r in areas} | {"SE": "Sweden"}
        f, why = _ratio(rows, region, "SE", "TAB5696", d.year, names)
        if f is None:
            left.append(LeftOut(factor="region", reason=why))
        else:
            factor, applied = factor * f, [*applied, "region"]
            inputs.append(TableRef(table="TAB5696", reference_year=d.year))
    if not applied:
        return None, "; ".join(lo.reason for lo in left)
    formula = {("age",): FORMULA, ("region",): REGION_FORMULA}.get(tuple(applied), BOTH_FORMULA)
    values = {p: None if getattr(d, p) is None else round(getattr(d, p) * factor)
              for p in PERCENTILES}
    return SimulatedPercentiles(age_band=age_band if "age" in applied else None,
                                region=region if "region" in applied else None, year=d.year,
                                formula=formula, inputs=inputs, applied=applied, left_out=left,
                                **values), None


def payload(code: str, on: dt.date, age_band: str | None = None, region: str | None = None,
            distributions: list[SalaryDistribution] | None = None,
            age_bands: list[AgeBandSalary] | None = None,
            regional: list[RegionalSalary] | None = None,
            titles: dict[str, tuple[str, str]] | None = None) -> SalaryPayload:
    from lonekrav.core.legal import load_registry

    if age_band is not None and age_band not in AGE_BANDS_:
        raise ValueError(f"age_band must be one of {list(AGE_BANDS_)}, not {age_band!r}")
    if region is not None and region not in REGIONS:
        raise ValueError(f"region must be one of {list(REGIONS)}, not {region!r}")
    dists = sorted((d for d in (distributions if distributions is not None
                                else load_distributions()) if d.code == code),
                   key=lambda d: d.year)
    ages_all = [a for a in (age_bands if age_bands is not None else load_age_bands())
                if a.code == code]
    latest = max((a.year for a in ages_all), default=None)
    ages = [a for a in ages_all if a.year == latest]

    reg = load_registry()
    median = reg.median_on(on)
    # Lines for the general rules in force on `on` (not the transition, which depends on the
    # applicant's permit history): the maintenance requirement before June 2026, the salary
    # requirement and its exempt level after (Copilot review on PR #2).
    rules = [r for r in LINE_RULES if median and reg.rule_active(r, on)]
    lines = [ThresholdLine(rule_id=r, percent=float(reg.rules[r].percent),
                           amount_sek=reg.threshold(r, median), median_sek=median.amount,
                           median_reference_year=median.scb_reference_year, on=on,
                           source=reg.rules[r].source)
             for r in rules]
    if code in reg.codes_on("banned", on) or not rules:
        applicable = None
    elif "salary_90" in rules:
        applicable = "salary_75_exempt" if code in reg.codes_on("exempt_75", on) else "salary_90"
    else:
        applicable = rules[0]

    simulated = note = None
    if (age_band or region) and not dists:
        note = "SCB publishes no salary figures for this code"
    elif age_band or region:
        areas = [r for r in (regional if regional is not None else load_regional())
                 if r.code == code] if region else []
        simulated, note = _simulate(dists[-1], age_band, ages_all, region, areas)
    sv, en = (titles or {}).get(code, ("", ""))
    return SalaryPayload(code=code, title_sv=sv, title_en=en, distributions=dists, age_bands=ages,
                         thresholds=lines, applicable_rule_id=applicable, simulated=simulated,
                         estimate_note=note, no_occupation_data=not dists)
