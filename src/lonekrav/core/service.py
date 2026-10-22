"""The operations every protocol adapter serves, over the data the app loads once (FR-002).

REST, MCP and the advisor call these methods and add nothing but transport: the not-found check,
the removal of ILO text and the salary defaults live here, not in an adapter (Principle I).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from lonekrav.core.adparse import AdText, ParsedAd, parse
from lonekrav.core.compare import CompareRequest, Comparison, compare
from lonekrav.core.eligibility import EligibilityAnswer, EligibilityRequest, UnknownCode, evaluate
from lonekrav.core.legal import Registry, TimelineEvent, load_registry
from lonekrav.core.legal_flags import flags_for
from lonekrav.core.models import AgeBandSalary, OccupationProfile, SalaryDistribution
from lonekrav.core.salary import SalaryPayload, payload
from lonekrav.core.search import SearchAnswer, SearchEngine, SearchRequest, run


@dataclass(frozen=True)
class Service:
    engine: SearchEngine
    profiles: dict[str, OccupationProfile]
    distributions: list[SalaryDistribution]
    age_bands: list[AgeBandSalary]

    def _known(self, code: str) -> OccupationProfile:
        if code not in self.profiles:
            raise UnknownCode(code)
        return self.profiles[code]

    def search(self, req: SearchRequest) -> SearchAnswer:
        return run(req, self.engine)

    def parse_ad(self, req: AdText) -> ParsedAd:
        return parse(req.text, self.engine.embedders["kblab"])

    def salary(self, code: str, on: dt.date | None = None,
               age_band: str | None = None) -> SalaryPayload:
        """Raises UnknownCode, or ValueError for an unknown age band."""
        p = self._known(code)
        return payload(code, on=on or dt.date.today(), age_band=age_band,
                       distributions=self.distributions, age_bands=self.age_bands,
                       titles={code: (p.title_sv, p.title_en)})

    def eligibility(self, req: EligibilityRequest) -> EligibilityAnswer:
        return evaluate(req, known_codes=self.profiles)

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

    def timeline(self) -> list[TimelineEvent]:
        return load_registry().timeline()

    def registry(self) -> Registry:
        return load_registry()
