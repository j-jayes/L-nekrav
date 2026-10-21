"""Official SCB salary statistics: Parquet storage and loading. Nothing is imputed."""

from __future__ import annotations

from pathlib import Path

import polars as pl

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
