"""The LegalConstants registry: every salary rule, median, code list and legal statement, with its
effective dates, source and checked-on date (constitution Principle II).

The data lives in `legal_constants.yaml`. Code reads dates and amounts from here and never writes
them itself, so the yearly June update touches only the YAML file.
"""

from __future__ import annotations

import datetime as dt
import itertools
from decimal import ROUND_HALF_UP, Decimal
from functools import cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel

REGISTRY_FILE = Path(__file__).with_name("legal_constants.yaml")


class Source(BaseModel):
    key: str
    title: str
    url: str
    checked_on: dt.date


class MedianRecord(BaseModel):
    amount: int
    scb_reference_year: int
    effective_from: dt.date
    effective_to: dt.date | None = None
    source: Source


class Rule(BaseModel):
    id: str
    kind: Literal["flat", "share_of_median"]
    percent: Decimal | None = None
    amount: int | None = None
    effective_from: dt.date | None
    effective_to: dt.date | None = None
    permits_granted_before: dt.date | None = None
    applies_to: str
    source: Source


class CodeList(BaseModel):
    kind: Literal["exempt_75", "banned", "partially_banned"]
    codes: dict[str, str]
    effective_from: dt.date
    effective_to: dt.date | None = None
    note: str
    source: Source


class PersonalExemption(BaseModel):
    id: str
    label: str
    conditions: str
    first_permit_only: bool
    source: Source


class Statement(BaseModel):
    id: str
    text: str
    source: Source


class MedianPublicationWindow(BaseModel):
    earliest: str  # "MM-DD"
    latest: str
    source: Source

    def day(self, which: Literal["earliest", "latest"], year: int) -> dt.date:
        month, day = map(int, getattr(self, which).split("-"))
        return dt.date(year, month, day)


class TimelineEvent(BaseModel):
    date: dt.date
    kind: Literal["median", "rule", "code_list"]
    summary: str
    source: Source


def round_half_up(x: Decimal) -> int:
    return int(x.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def sek(n: int) -> str:
    return f"{n:,}".replace(",", " ") + " SEK"


def _active(row, on: dt.date) -> bool:
    return ((row.effective_from is None or row.effective_from <= on)
            and (row.effective_to is None or on <= row.effective_to))


class Registry(BaseModel):
    medians: list[MedianRecord]
    median_publication_window: MedianPublicationWindow
    rules: dict[str, Rule]
    code_lists: dict[str, CodeList]
    exemptions: dict[str, PersonalExemption]
    statements: dict[str, Statement]

    def median_on(self, on: dt.date) -> MedianRecord | None:
        """The median in force on a day: from the day it takes effect, inclusive."""
        return next((m for m in reversed(self.medians) if _active(m, on)), None)

    def threshold(self, rule_id: str, median: MedianRecord) -> int:
        rule = self.rules[rule_id]
        if rule.kind == "flat":
            return rule.amount
        return round_half_up(rule.percent * median.amount / 100)

    def rule_active(self, rule_id: str, on: dt.date) -> bool:
        return _active(self.rules[rule_id], on)

    def codes_on(self, kind: str, on: dt.date) -> dict[str, str]:
        cl = self.code_lists[kind]
        return dict(cl.codes) if _active(cl, on) else {}

    def median_due(self, on: dt.date) -> bool:
        """A new median may have been published: on or after the year's earliest publication day
        with no median that took effect that year (FR-005)."""
        return (on >= self.median_publication_window.day("earliest", on.year)
                and not any(m.effective_from.year == on.year for m in self.medians))

    def registry_is_current(self, today: dt.date) -> bool:
        """False once the year's latest publication day has passed without a new median (FR-005a)."""
        if today <= self.median_publication_window.day("latest", today.year):
            return True
        return any(m.effective_from.year == today.year for m in self.medians)

    def timeline(self) -> list[TimelineEvent]:
        ev = [TimelineEvent(date=m.effective_from, kind="median",
                            summary=f"Median {sek(m.amount)} (SCB {m.scb_reference_year}) applies to "
                                    "applications filed from this day", source=m.source)
              for m in self.medians]
        for r in self.rules.values():
            what = sek(r.amount) if r.kind == "flat" else f"{r.percent} % of the median"
            if r.effective_from:
                ev.append(TimelineEvent(date=r.effective_from, kind="rule",
                                        summary=f"From this day: {what}. {r.applies_to}",
                                        source=r.source))
            if r.effective_to:
                ev.append(TimelineEvent(date=r.effective_to, kind="rule",
                                        summary=f"Last day: {what}. {r.applies_to}",
                                        source=r.source))
        for cl in self.code_lists.values():
            ev.append(TimelineEvent(date=cl.effective_from, kind="code_list",
                                    summary=f"{cl.kind} list ({len(cl.codes)} codes). {cl.note}",
                                    source=cl.source))
        return sorted(ev, key=lambda e: e.date)


def _with_source(section: str, key, row: dict, sources: dict[str, Source]) -> dict:
    if row.get("source") not in sources:
        raise ValueError(f"{section}[{key}]: missing or unknown source {row.get('source')!r}")
    return {**row, "source": sources[row["source"]]}


@cache
def load_registry(path: Path = REGISTRY_FILE) -> Registry:
    raw = yaml.safe_load(Path(path).read_text())
    sources = {k: Source(key=k, **v) for k, v in raw["sources"].items()}
    medians = [_with_source("medians", i, r, sources) for i, r in enumerate(raw["medians"])]
    medians.sort(key=lambda r: r["effective_from"])
    for a, b in itertools.pairwise(medians):
        a["effective_to"] = b["effective_from"] - dt.timedelta(days=1)
    keyed = {name: {k: _with_source(name, k, {"id": k, **v}, sources)
                    for k, v in raw[name].items()}
             for name in ("rules", "exemptions", "statements")}
    code_lists = {k: _with_source("code_lists", k, {"kind": k, **v}, sources)
                  for k, v in raw["code_lists"].items()}
    return Registry(
        medians=medians,
        median_publication_window=_with_source("median_publication_window", 0,
                                               raw["median_publication_window"], sources),
        code_lists=code_lists, **keyed,
    )
