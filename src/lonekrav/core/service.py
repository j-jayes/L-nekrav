"""The operations every protocol adapter serves, over the data the app loads once (FR-002).

REST, MCP and the advisor call these methods and add nothing but transport: the not-found check,
the removal of ILO text and the salary defaults live here, not in an adapter (Principle I).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from lonekrav.core.adparse import AdText, ParsedAd, parse
from lonekrav.core.compare import CompareRequest, Comparison, compare
from lonekrav.core.eligibility import EligibilityAnswer, EligibilityRequest, UnknownCode, evaluate
from lonekrav.core.legal import Registry, TimelineEvent, load_registry
from lonekrav.core.legal_flags import flags_for
from lonekrav.core.market import LiveCache, MarketAnswer, market
from lonekrav.core.models import (
    AgeBandSalary,
    OccupationProfile,
    RegionalSalary,
    SalaryDistribution,
    YearlyAds,
)
from lonekrav.core.occupation_map import (
    Closeness,
    MapAnswer,
    NeighbourAnswer,
    OccupationMap,
    ServedPoint,
    SimilarCode,
    closeness,
)
from lonekrav.core.salary import SalaryPayload, payload, position
from lonekrav.core.search import SearchAnswer, SearchEngine, SearchRequest, run


@dataclass(frozen=True)
class Service:
    engine: SearchEngine
    profiles: dict[str, OccupationProfile]
    distributions: list[SalaryDistribution]
    age_bands: list[AgeBandSalary]
    regional: list[RegionalSalary] = field(default_factory=list)
    history: list[YearlyAds] = field(default_factory=list)
    live: LiveCache = field(default_factory=LiveCache)
    occupation_map: OccupationMap | None = None  # Feature 007; codes and numbers only
    similarity: dict[tuple[str, str], float] = field(default_factory=dict)  # (code_a < code_b)

    def _known(self, code: str) -> OccupationProfile:
        if code not in self.profiles:
            raise UnknownCode(code)
        return self.profiles[code]

    def search(self, req: SearchRequest) -> SearchAnswer:
        return run(req, self.engine)

    def parse_ad(self, req: AdText) -> ParsedAd:
        return parse(req.text, self.engine.embedders["kblab"])

    def salary(self, code: str, on: dt.date | None = None, age_band: str | None = None,
               region: str | None = None) -> SalaryPayload:
        """Raises UnknownCode, or ValueError for an unknown age band or area."""
        p = self._known(code)
        return payload(code, on=on or dt.date.today(), age_band=age_band, region=region,
                       distributions=self.distributions, age_bands=self.age_bands,
                       regional=self.regional,
                       titles={code: (p.title_sv, p.title_en)})

    def eligibility(self, req: EligibilityRequest) -> EligibilityAnswer:
        answer = evaluate(req, known_codes=self.profiles)
        latest = max((d for d in self.distributions if d.code == req.code),
                     key=lambda d: d.year, default=None)
        if latest is None:
            return answer
        fte = round(req.monthly_salary_sek * 100 / req.fte_percent)
        return answer.model_copy(update={"market_position": position(fte, latest)})

    def compare(self, req: CompareRequest) -> Comparison:
        for code in req.codes:
            self._known(code)
        return compare(req, profiles=self.profiles, distributions=self.distributions,
                       age_bands=self.age_bands)

    def occupation(self, code: str) -> OccupationProfile:
        """The profile with registry legal flags; ILO text is never served (ILO reserves rights)."""
        p = self._known(code)
        return p.model_copy(update={
            "legal_flags": flags_for(code),
            "descriptions": [d for d in p.descriptions if d.source.source != "ilo_isco08"]})

    def market(self, code: str) -> MarketAnswer:
        """Open ads now, regional means and yearly ads for a code: context, never a reason to
        choose it. A live failure is part of the answer, not an exception (FR-005)."""
        return market(self._known(code), self.profiles, self.live, self.regional, self.history)

    def _medians(self) -> dict[str, tuple[int | None, int]]:
        latest = {}
        for d in self.distributions:
            if d.year >= latest.get(d.code, (None, 0))[1]:
                latest[d.code] = (d.median, d.year)
        return latest

    def _similar(self, code: str, cosine: float, medians: dict) -> SimilarCode:
        p = self.profiles.get(code)
        median, year = medians.get(code, (None, None))
        near = closeness(code, code, cosine, self.occupation_map.pair_quantiles)
        return SimilarCode(code=code, title_sv=p and p.title_sv, title_en=p and p.title_en,
                           cosine=cosine, percentile=near.percentile,
                           same_description=near.same_description, median_sek=median,
                           median_year=year)

    def map(self) -> MapAnswer:
        """Every mapped code the service knows, with titles, latest median and flags (007 FR-010)."""
        m, medians = self.occupation_map, self._medians()
        points = []
        for pt in m.points:
            if (p := self.profiles.get(pt.code)) is None:
                continue
            median, year = medians.get(pt.code, (None, None))
            points.append(ServedPoint(**pt.model_dump(), title_sv=p.title_sv, title_en=p.title_en,
                                      median_sek=median, median_year=year,
                                      legal_flags=[f.kind for f in flags_for(pt.code)]))
        return MapAnswer(model=m.model, umap=m.umap, built_on=m.built_on, stale=m.stale,
                         pair_quantiles=m.pair_quantiles, major_groups=m.major_groups, points=points)

    def neighbours(self, code: str, k: int = 10) -> NeighbourAnswer:
        """Raises UnknownCode, or ValueError for k outside 1-10."""
        self._known(code)
        if not 1 <= k <= 10:
            raise ValueError(f"k must be between 1 and 10, not {k}")
        point = next(p for p in self.occupation_map.points if p.code == code)
        medians = self._medians()
        return NeighbourAnswer(code=code, neighbours=[
            self._similar(n.code, n.cosine, medians) for n in point.neighbours[:k]])

    def closeness(self, a: str, b: str) -> Closeness:
        """Raises UnknownCode, or ValueError when a and b are the same code."""
        self._known(a)
        self._known(b)
        if a == b:
            raise ValueError("a and b must be two different codes")
        return closeness(a, b, self.similarity[tuple(sorted((a, b)))],
                         self.occupation_map.pair_quantiles)

    def timeline(self) -> list[TimelineEvent]:
        return load_registry().timeline()

    def registry(self) -> Registry:
        """The legal registry, with each listed code named by its Swedish title (FR-022); a note
        the registry gives a code (9210's berry pickers) follows the title."""
        reg = load_registry()
        lists = {kind: cl.model_copy(update={"codes": {
            code: ": ".join(t for t in (self.profiles[code].title_sv if code in self.profiles
                                        else "", note) if t)
            for code, note in cl.codes.items()}}) for kind, cl in reg.code_lists.items()}
        return reg.model_copy(update={"code_lists": lists})
