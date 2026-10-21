"""Does an offer meet the salary requirement for a Swedish work permit? (spec Story 1)

Every date, percentage and amount comes from the legal registry; this module only decides which
registry row applies (data-model.md, "Rule selection").
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Container
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from lonekrav.core.legal import MedianRecord, Registry, Source, load_registry, sek

DISCLAIMER = ("The salary must also be in line with the collective agreement or what is customary "
              "in the occupation or industry, which Lönekrav does not check. This is information, "
              "not legal advice.")


class UnknownCode(KeyError):
    def __str__(self) -> str:
        return f"unknown SSYK code {self.args[0]!r}"


class EligibilityRequest(BaseModel):
    code: str = Field(pattern=r"^\d{4}$")
    monthly_salary_sek: int = Field(gt=0, description="Gross monthly salary actually paid")
    fte_percent: int = Field(ge=1, le=100, description="Share of full time")
    application_type: Literal["first_permit", "extension"]
    filed_on: dt.date
    decided_on: dt.date = Field(default_factory=dt.date.today,
                                description="Expected decision date; defaults to today")
    current_permit_granted_on: dt.date | None = Field(
        default=None, description="Decision date of the current permit (extensions only)")
    exemptions: list[str] = Field(default=[], description="Declared personal exemption ids")

    @field_validator("exemptions")
    @classmethod
    def _known_and_unique(cls, v: list[str]) -> list[str]:
        known = load_registry().exemptions
        if unknown := [e for e in v if e not in known]:
            raise ValueError(f"unknown exemptions {unknown}; expected some of {sorted(known)}")
        if len(set(v)) != len(v):
            raise ValueError("exemptions must be unique")
        return v

    @model_validator(mode="after")
    def _consistent(self):
        if (self.application_type == "extension") != (self.current_permit_granted_on is not None):
            raise ValueError("current_permit_granted_on is required for an extension and only "
                             "allowed for one")
        if self.decided_on < self.filed_on:
            raise ValueError("decided_on cannot be before filed_on")
        exemptions = load_registry().exemptions
        if self.application_type == "extension" and any(
                exemptions[e].first_permit_only for e in self.exemptions):
            raise ValueError("exemptions: former_student_researcher applies to first permits only")
        return self


class Warning(BaseModel):
    kind: Literal["part_time", "stale_median", "partial_ban"]
    message: str
    source: Source


class EligibilityAnswer(BaseModel):
    status: Literal["pass", "fail", "not_permitted", "out_of_scope"]
    rule_id: str | None = None
    reason: str
    percent: float | None = None
    median: MedianRecord | None = None
    threshold_sek: int | None = None
    margin_sek: int | None = None
    margin_percent: float | None = None
    warnings: list[Warning] = []
    sources: list[Source]
    disclaimer: str = DISCLAIMER


def _unique(sources: list[Source]) -> list[Source]:
    return list({s.key: s for s in sources}.values())


def _warnings(req: EligibilityRequest, reg: Registry, median: MedianRecord | None) -> list[Warning]:
    out = []
    if req.code in reg.codes_on("partially_banned", req.decided_on):
        st = reg.statements["partial_ban_9210"]
        out.append(Warning(kind="partial_ban", message=st.text, source=st.source))
    if req.fte_percent < 100:
        st = reg.statements["part_time"]
        out.append(Warning(kind="part_time", message=st.text, source=st.source))
    if median and reg.median_due(req.decided_on):
        out.append(Warning(kind="stale_median", source=median.source, message=(
            f"SCB publishes a new median every June and it may already apply. This answer uses "
            f"{sek(median.amount)} (SCB {median.scb_reference_year}), the newest in Lönekrav's "
            "registry.")))
    return out


def _rule(req: EligibilityRequest, reg: Registry) -> tuple[str, str, list[Source]]:
    """(rule id, reason, sources that decided it) for a request that is in scope."""
    t = reg.rules["transition_maintenance_80"]
    if (req.application_type == "extension"
            and t.effective_from <= req.filed_on <= t.effective_to
            and req.current_permit_granted_on < t.permits_granted_before):
        return t.id, t.applies_to, [t.source]
    exempt = reg.code_lists["exempt_75"]
    if req.code in reg.codes_on("exempt_75", req.decided_on):
        return "salary_75_exempt", f"Occupation {req.code} is on the exempt list. {exempt.note}", \
            [exempt.source]
    if req.exemptions:
        ex = [reg.exemptions[e] for e in req.exemptions]
        why = "; ".join(f"{e.label}: {e.conditions}" for e in ex)
        return "salary_75_exempt", f"Declared exemption. {why}", [e.source for e in ex]
    return "salary_90", reg.rules["salary_90"].applies_to, []


def evaluate(req: EligibilityRequest, registry: Registry | None = None,
             known_codes: Container[str] | None = None) -> EligibilityAnswer:
    reg = registry or load_registry()
    if known_codes is not None and req.code not in known_codes:
        raise UnknownCode(req.code)
    median = reg.median_on(req.filed_on)
    warnings = _warnings(req, reg, median)

    if req.code in reg.codes_on("banned", req.decided_on):
        banned = reg.code_lists["banned"]
        return EligibilityAnswer(status="not_permitted", reason=banned.note, warnings=warnings,
                                 sources=_unique([banned.source, *(w.source for w in warnings)]))

    new_rule = reg.rules["salary_90"].effective_from
    decisive = req.decided_on if req.application_type == "first_permit" else req.filed_on
    if decisive < new_rule or median is None:
        st = reg.statements["out_of_scope"]
        return EligibilityAnswer(status="out_of_scope", reason=st.text, warnings=warnings,
                                 sources=_unique([st.source, *(w.source for w in warnings)]))

    rule_id, reason, decided_by = _rule(req, reg)
    rule = reg.rules[rule_id]
    threshold = reg.threshold(rule_id, median)
    margin = req.monthly_salary_sek - threshold
    return EligibilityAnswer(
        status="pass" if margin >= 0 else "fail", rule_id=rule_id, reason=reason,
        percent=float(rule.percent), median=median, threshold_sek=threshold, margin_sek=margin,
        margin_percent=round(margin / threshold * 100, 1), warnings=warnings,
        sources=_unique([rule.source, median.source, *decided_by,
                         *(w.source for w in warnings)]))
