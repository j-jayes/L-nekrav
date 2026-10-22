"""MCP adapter (contracts/mcp.md): the same operations and models as /api/v1, as tools and resources.

Each tool is one call into `app.state.service`; the tools read it when called, so one server
built at start-up serves the data the lifespan loads (research R3).
"""

from __future__ import annotations

import datetime as dt
import logging
from collections.abc import Iterator
from contextlib import contextmanager

from fastmcp import FastMCP
from fastmcp.exceptions import ResourceError, ToolError

from lonekrav.core.adparse import AdText, ParsedAd
from lonekrav.core.compare import CompareRequest, Comparison
from lonekrav.core.eligibility import EligibilityAnswer, EligibilityRequest, UnknownCode
from lonekrav.core.salary import SalaryPayload
from lonekrav.core.search import SearchAnswer, SearchRequest
from lonekrav.core.service import Service


@contextmanager
def _expected(error: type[Exception] = ToolError) -> Iterator[None]:
    """Unknown codes and age bands reach the client with REST's text; anything else is masked."""
    try:
        yield
    except (UnknownCode, ValueError) as e:
        raise error(str(e)) from e


def build_mcp(app) -> FastMCP:
    # fastmcp logs every tool's arguments at DEBUG; never let it go below INFO (FR-005).
    fastmcp_log = logging.getLogger("fastmcp")
    fastmcp_log.setLevel(max(logging.INFO, fastmcp_log.level))
    mcp = FastMCP("lonekrav", mask_error_details=True, instructions=(
        "Swedish work-permit salary requirements by SSYK 2012 occupation code. Every result "
        "names its sources; the code on an offer must match the duties actually performed."))

    def service() -> Service:
        return app.state.service

    @mcp.tool
    def search_occupations(request: SearchRequest) -> SearchAnswer:
        """Find the SSYK 2012 occupation codes that best fit a job title, description or pasted
        job ad, in English or Swedish. Use mode "full" for long or unusual text, and parse_ad for
        a whole ad so only the passages describing the job are searched."""
        return service().search(request)

    @mcp.tool
    def extract_job_ad_signal(request: AdText) -> ParsedAd:
        """Split a pasted job ad into passages labelled title, duty, skill, company, benefits or
        other, and return the text that describes the job itself."""
        return service().parse_ad(request)

    @mcp.tool
    def get_occupation_salary(code: str, age_band: str | None = None,
                              on: dt.date | None = None) -> SalaryPayload:
        """SCB salary distribution for a four-digit SSYK code, the work-permit salary thresholds
        in force on date `on` (default today), and, for an age band such as "25-34", simulated
        age-adjusted figures marked is_simulated."""
        with _expected():
            return service().salary(code, on=on, age_band=age_band)

    @mcp.tool
    def evaluate_permit_eligibility(request: EligibilityRequest) -> EligibilityAnswer:
        """Check whether an offer (code, monthly salary, share of full time, application type and
        dates) meets the work-permit salary requirement, with the rule, threshold, margin,
        warnings and legal sources."""
        with _expected():
            return service().eligibility(request)

    @mcp.tool
    def compare_occupations(request: CompareRequest) -> Comparison:
        """Compare 2–5 SSYK codes side by side: official task descriptions, latest salaries,
        legal flags and thresholds, and eligibility for an optional offer."""
        with _expected():
            return service().compare(request)

    @mcp.resource("legal://timeline", mime_type="application/json")
    def legal_timeline() -> list[dict]:
        """Every dated work-permit salary rule and median, with its source and checked-on date."""
        return [e.model_dump(mode="json") for e in service().timeline()]

    @mcp.resource("ssyk://{code}", mime_type="application/json")
    def ssyk_profile(code: str) -> dict:
        """The profile of one SSYK 2012 code: titles, descriptions, synonyms and legal flags."""
        with _expected(ResourceError):
            return service().occupation(code).model_dump(mode="json")

    return mcp
