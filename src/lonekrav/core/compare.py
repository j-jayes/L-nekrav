"""Two to five occupation codes side by side (spec Story 6, FR-027, FR-028).

Each column shows the official task text and the consequences of that code; columns stay in the
order the user gave, never ranked by threshold (Principle III).
"""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field, field_validator

from lonekrav.core.eligibility import EligibilityAnswer, EligibilityRequest, Offer, evaluate
from lonekrav.core.legal_flags import flags_for
from lonekrav.core.models import (
    AgeBandSalary,
    LegalFlag,
    OccupationProfile,
    SalaryDistribution,
    Text,
)
from lonekrav.core.salary import ThresholdLine, payload
from lonekrav.core.search import HONEST_FIT

SWEDISH_SOURCES = ("scb_mis2012", "jobtech")  # SCB's SSYK publication first, then JobTech's


class CompareRequest(BaseModel):
    codes: list[str] = Field(description="2–5 distinct SSYK codes, in the order to show them")
    offer: Offer | None = None

    @field_validator("codes")
    @classmethod
    def _two_to_five(cls, v: list[str]) -> list[str]:
        v = list(dict.fromkeys(v))
        if not 2 <= len(v) <= 5:
            raise ValueError(f"codes: give 2–5 distinct codes, got {len(v)}")
        return v


class CompareColumn(BaseModel):
    code: str
    title_sv: str
    title_en: str
    tasks_sv: list[Text]
    tasks_en: list[Text]
    latest: SalaryDistribution | None
    legal_flags: list[LegalFlag]
    threshold: ThresholdLine | None  # with an offer: the threshold its eligibility answer used
    eligibility: EligibilityAnswer | None = None


class Comparison(BaseModel):
    columns: list[CompareColumn]
    honest_fit: str = HONEST_FIT


def _tasks_sv(p: OccupationProfile) -> list[Text]:
    for source in SWEDISH_SOURCES:
        if texts := [d for d in p.descriptions if d.lang == "sv" and d.source.source == source]:
            return texts
    return []


def _line(a: EligibilityAnswer, on: dt.date) -> ThresholdLine | None:
    """The threshold an eligibility answer used; none when the code is not permitted or the
    offer is out of scope (Copilot review on PR #2: the code-only line could contradict it)."""
    if a.threshold_sek is None:
        return None
    return ThresholdLine(rule_id=a.rule_id, percent=a.percent, amount_sek=a.threshold_sek,
                         median_sek=a.median.amount,
                         median_reference_year=a.median.scb_reference_year, on=on)


def compare(req: CompareRequest, profiles: dict[str, OccupationProfile],
            distributions: list[SalaryDistribution] | None = None,
            age_bands: list[AgeBandSalary] | None = None) -> Comparison:
    """Raises KeyError for a code with no profile."""
    on = req.offer.filed_on if req.offer else dt.date.today()
    columns = []
    for code in req.codes:
        p = profiles[code]
        pay = payload(code, on=on, distributions=distributions, age_bands=age_bands)
        line = next((t for t in pay.thresholds if t.rule_id == pay.applicable_rule_id), None)
        answer = None
        if req.offer:
            answer = evaluate(EligibilityRequest(code=code, **req.offer.model_dump()))
            line = _line(answer, on)
        columns.append(CompareColumn(
            code=code, title_sv=p.title_sv, title_en=p.title_en, tasks_sv=_tasks_sv(p),
            tasks_en=[d for d in p.descriptions if d.lang == "en" and d.source.source == "esco"],
            latest=pay.distributions[-1] if pay.distributions else None,
            legal_flags=flags_for(code), threshold=line, eligibility=answer))
    return Comparison(columns=columns)
