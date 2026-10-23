"""Pydantic models shared by every Lönekrav surface (CLI, REST, MCP, A2A, React).

Field meanings are documented in specs/001-data-taxonomy-index/data-model.md.
"""

from __future__ import annotations

import datetime as dt
import itertools
from typing import Literal

from pydantic import BaseModel, Field, computed_field, model_validator

Lang = Literal["sv", "en"]
Source = Literal[
    "scb_structure", "scb_english", "scb_title_index", "scb_isco_key", "scb_mis2012",
    "scb_pxweb", "jobtech", "ilo_isco08", "esco", "sfs", "jobtech_jobsearch", "jobtech_historical",
]
Code = str  # four digits, validated where it is a key


class SourceRef(BaseModel):
    source: Source
    ref: str
    url: str


class Text(BaseModel):
    lang: Lang
    kind: Literal["definition", "tasks", "included_occupations", "excluded"]
    text: str = Field(min_length=1)
    source: SourceRef
    isco_code: str | None = None
    shared_with: list[Code] = []


class Synonym(BaseModel):
    lang: Lang
    label: str = Field(min_length=1)
    source: SourceRef
    jobtech_id: str | None = None
    esco_uri: str | None = None
    match_type: Literal["exact", "close", "broad", "narrow"] | None = None


def dedupe_synonyms(synonyms: list[Synonym]) -> list[Synonym]:
    """Keep the first synonym per (language, case-folded label); callers order by precedence."""
    seen: set[tuple[str, str]] = set()
    kept = []
    for s in synonyms:
        key = (s.lang, s.label.casefold().strip())
        if key not in seen:
            seen.add(key)
            kept.append(s)
    return kept


class LegalFlag(BaseModel):
    kind: Literal["exempt_75", "banned", "partially_banned"]
    note: str = ""
    effective_from: dt.date
    source: SourceRef
    checked_on: dt.date | None = None  # from the legal registry; absent in profiles built by 001


class OccupationProfile(BaseModel):
    code: Code = Field(pattern=r"^\d{4}$")
    title_sv: str = Field(min_length=1)
    title_en: str = Field(min_length=1)
    isco_codes: list[str] = Field(min_length=1)
    jobtech_concept_id: str | None = None
    jobtech_shared: bool = False
    descriptions: list[Text]
    synonyms: list[Synonym] = []
    legal_flags: list[LegalFlag] = []
    sources: list[SourceRef]

    @model_validator(mode="after")
    def _has_swedish_description(self):
        if not any(d.lang == "sv" for d in self.descriptions):
            raise ValueError(f"{self.code}: profile needs at least one Swedish description")
        return self


VALUE_FIELDS = ("mean", "median", "p10", "p25", "p75", "p90")
ORDERED = ("p10", "p25", "median", "p75", "p90")


class SalaryDistribution(BaseModel):
    code: Code = Field(pattern=r"^\d{4}$")
    year: int = Field(ge=2014)
    mean: int | None
    median: int | None
    p10: int | None
    p25: int | None
    p75: int | None
    p90: int | None
    mean_ci95: int | None = None
    median_ci95: int | None = None
    p10_ci95: int | None = None
    p25_ci95: int | None = None
    p75_ci95: int | None = None
    p90_ci95: int | None = None
    source_table: Literal["TAB4265", "TAB5932"]
    reference_year: int
    fetched_at: dt.datetime

    @computed_field
    @property
    def suppressed(self) -> list[str]:
        return [f for f in VALUE_FIELDS if getattr(self, f) is None]

    @model_validator(mode="after")
    def _check(self):
        if self.reference_year != self.year:
            raise ValueError(f"{self.code} {self.year}: reference_year {self.reference_year}")
        present = [(f, getattr(self, f)) for f in ORDERED if getattr(self, f) is not None]
        for (fa, a), (fb, b) in itertools.pairwise(present):
            if a > b:
                raise ValueError(f"{self.code} {self.year}: {fa}={a} > {fb}={b} in SCB data")
        return self


class AgeBandSalary(BaseModel):
    code: Code = Field(pattern=r"^\d{4}$")
    year: int = Field(ge=2014)
    age_band: Literal["18-24", "25-34", "35-44", "45-54", "55-64", "65-68", "all"]
    mean_monthly: int | None
    headcount: int | None
    mean_ci95: int | None = None
    source_table: Literal["TAB4264", "TAB5844"]
    reference_year: int
    fetched_at: dt.datetime

    @computed_field
    @property
    def suppressed(self) -> list[str]:
        return [f for f in ("mean_monthly", "headcount") if getattr(self, f) is None]

    @model_validator(mode="after")
    def _check(self):
        if self.reference_year != self.year:
            raise ValueError(f"{self.code} {self.year}: reference_year {self.reference_year}")
        return self


class RegionalSalary(BaseModel):
    """SCB's mean monthly salary for one code in Sweden (SE) or one national area (Feature 005).
    A mean, not the median the salary floor is based on; each figure is null where SCB suppresses
    it, independently of the others."""
    code: Code = Field(pattern=r"^\d{4}$")
    year: int = Field(ge=2023)
    region: str
    region_name: str
    mean: int | None
    mean_ci95: int | None = None  # ± margin, as SCB publishes it
    employees: int | None
    source_table: Literal["TAB5696"]
    reference_year: int
    fetched_at: dt.datetime

    @computed_field
    @property
    def suppressed(self) -> list[str]:
        return [f for f in ("mean", "employees") if getattr(self, f) is None]

    @model_validator(mode="after")
    def _check(self):
        if self.reference_year != self.year:
            raise ValueError(f"{self.code} {self.year}: reference_year {self.reference_year}")
        return self


class YearlyAds(BaseModel):
    """Ads published on Platsbanken in one full calendar year for one JobTech occupation group."""
    concept_id: str
    year: int = Field(ge=2016)  # the historical interface has no coded ads before 2016
    ads: int = Field(ge=0)
    source: Literal["jobtech_historical"] = "jobtech_historical"
    fetched_at: dt.datetime  # when this count was fetched (deterministic builds)
