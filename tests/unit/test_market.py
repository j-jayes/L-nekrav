"""Market pulse in core: live demand, its cache, and the market answer (Feature 005)."""

import datetime as dt
import json

import httpx
import pytest

from lonekrav.core.market import (
    JOBSEARCH_URL,
    MARKET_NOTICE,
    TTL,
    LiveCache,
    market,
    parse_live,
)

T0 = dt.datetime(2026, 10, 23, 9, tzinfo=dt.UTC)
CONCEPT = "DJh5_yyF_hEM"  # 2512


@pytest.fixture
def bodies(fixtures):
    j = fixtures / "jobsearch"
    return (json.loads((j / "live_2512_plain.json").read_text()),
            json.loads((j / "live_2512.json").read_text()))


class Clock:
    def __init__(self):
        self.now = T0

    def __call__(self):
        return self.now


class FakeApi:
    """Answers like JobSearch: the plain body without stats, the stats body with them."""

    def __init__(self, plain, stats, error=None):
        self.plain, self.stats, self.error, self.calls = plain, stats, error, []

    def __call__(self, url, params):
        self.calls.append((url, params))
        if self.error:
            raise self.error
        return self.stats if "stats" in params else self.plain


def test_parse_live_counts_counties_and_ads_without_a_county(bodies):
    plain, stats = bodies
    d = parse_live(CONCEPT, plain, stats, fetched_at=T0, url=JOBSEARCH_URL)
    assert (d.status, d.ads, d.positions) == ("available", 1185, 1571)
    counts = [c.ads for c in d.counties]
    assert counts == sorted(counts, reverse=True)
    assert d.counties[0].name == "Stockholms län" and d.counties[0].code == "01"
    assert d.no_county == 1185 - sum(counts) == 19
    assert d.fetched_at == T0 and d.concept_id == CONCEPT
    assert d.source.source == "jobtech_jobsearch" and CONCEPT in d.source.url


def test_parse_live_rejects_a_body_without_a_total(bodies):
    with pytest.raises(ValueError):
        parse_live(CONCEPT, {"hits": []}, bodies[1], fetched_at=T0, url=JOBSEARCH_URL)


def test_live_cache_makes_two_requests_and_reuses_the_answer_for_15_minutes(bodies):
    api, clock = FakeApi(*bodies), Clock()
    cache = LiveCache(get_json=api, clock=clock)
    first = cache.get(CONCEPT)
    assert len(api.calls) == 2  # positions only come without stats (research R1)
    clock.now = T0 + TTL - dt.timedelta(seconds=1)
    again = cache.get(CONCEPT)
    assert len(api.calls) == 2 and again.fetched_at == first.fetched_at == T0
    clock.now = T0 + TTL
    assert cache.get(CONCEPT).fetched_at == T0 + TTL and len(api.calls) == 4


REQUEST = httpx.Request("GET", JOBSEARCH_URL)


@pytest.mark.parametrize(("error", "reason"), [
    (httpx.ReadTimeout("slow"), "timeout"),
    (httpx.ConnectError("refused"), "connection error"),
    (httpx.HTTPStatusError("503", request=REQUEST, response=httpx.Response(503, request=REQUEST)),
     "http 503"),
    (json.JSONDecodeError("bad", "", 0), "unexpected response"),
])
def test_failures_are_unavailable_with_a_reason_and_no_number(bodies, error, reason):
    api = FakeApi(*bodies, error=error)
    cache = LiveCache(get_json=api, clock=Clock())
    d = cache.get(CONCEPT)
    assert (d.status, d.reason) == ("unavailable", reason)
    assert d.ads is d.positions is d.no_county is None and d.counties == []
    api.error = None
    assert cache.get(CONCEPT).status == "available"  # a failure is not reused


def test_market_names_codes_that_share_a_concept(inputs):
    from lonekrav.core.profiles import build_profiles

    profiles = build_profiles(inputs)
    api = FakeApi({"total": {"value": 3}, "positions": 4}, {"total": {"value": 3}, "stats": [
        {"type": "region", "values": [{"term": "Skåne län", "code": "12", "count": 3}]}]})
    answer = market(profiles["1211"], profiles, LiveCache(get_json=api, clock=Clock()), [], [])
    assert answer.shared_with == ["1212"]
    assert answer.live.status == "available" and answer.live.ads == 3


def test_market_without_a_concept_makes_no_request(inputs):
    from lonekrav.core.profiles import build_profiles

    profiles = build_profiles(inputs)
    assert profiles["4430"].jobtech_concept_id is None
    api = FakeApi({}, {})
    answer = market(profiles["4430"], profiles, LiveCache(get_json=api, clock=Clock()), [], [])
    assert answer.live.status == "no_concept" and answer.live.ads is None
    assert answer.history_status == "no_concept" and answer.history == []
    assert api.calls == [] and answer.shared_with == []


def test_market_notice_carries_the_honest_fit_rule():
    from lonekrav.core.search import HONEST_FIT

    rule = HONEST_FIT.split(". ")[0]  # "The SSYK code ... must match the duties actually performed"
    assert rule in MARKET_NOTICE
    assert "mean" in MARKET_NOTICE and "national median" in MARKET_NOTICE


def test_market_shows_the_latest_regional_year_with_sweden_first(inputs, fixtures):
    from lonekrav.core.profiles import build_profiles
    from lonekrav.etl.scb_pxweb import parse_regional

    profiles = build_profiles(inputs)
    regional = parse_regional(fixtures / "pxweb/TAB5696.json", T0)
    live = LiveCache(get_json=FakeApi({}, {}, error=httpx.ConnectError("x")), clock=Clock())
    a = market(profiles["2512"], profiles, live, regional, [])
    assert a.regional_year == 2025 and {r.year for r in a.regional} == {2025}
    assert [r.region for r in a.regional] == ["SE", "SE11", "SE12", "SE21", "SE22", "SE23",
                                              "SE31", "SE32", "SE33"]
    assert all(r.code == "2512" for r in a.regional)
    empty = market(profiles["2512"], profiles, live, [r for r in regional if r.code != "2512"], [])
    assert empty.regional == [] and empty.regional_year is None


def test_market_history_is_the_concepts_years_in_order(inputs):
    from lonekrav.core.models import YearlyAds
    from lonekrav.core.profiles import build_profiles

    profiles = build_profiles(inputs)
    rows = [YearlyAds(concept_id=c, year=y, ads=n, fetched_at=T0)
            for c, y, n in [(CONCEPT, 2025, 30304), ("other", 2016, 5), (CONCEPT, 2016, 16406)]]
    live = LiveCache(get_json=FakeApi({}, {}, error=httpx.ConnectError("x")), clock=Clock())
    a = market(profiles["2512"], profiles, live, [], rows)
    assert a.history_status == "available"
    assert [(h.year, h.ads) for h in a.history] == [(2016, 16406), (2025, 30304)]
    assert market(profiles["4430"], profiles, live, [], rows).history == []
