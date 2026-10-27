# Implementation Plan: Your number

**Branch**: `006-your-number` | **Date**: 2026-10-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/006-your-number/spec.md`

## Summary

The page is reframed around the candidate's question: *what number should I ask for?* Three core
additions, each served on every surface, back it:

- **Market position**: `core.salary.position` places a full-time-equivalent amount between SCB's
  published percentiles, with no interpolation. It is returned on the eligibility answer (R1).
- **Estimate**: the existing age simulation gains an area factor from TAB5696, with each factor
  applied or left out with a reason (R2).
- **Floor sources**: threshold lines carry their legal source (R3).

On the page, the compare view becomes step 2, "Your number". It is one card per code with a
headline, the position, the estimate and the floor check; the detail sits behind expanders. The
salary chart is redrawn around the middle half of the market and the candidate's number. The tabs
become numbered steps (R5, R6).

## Technical Context

**Language/Version**: Python 3.12 (uv); TypeScript 5.9 on Node 22 for the page.

**Primary Dependencies**: no new ones.

**Storage**: no new artefacts. The salary, age and regional Parquet files already hold every input.

**Testing**:
- pytest for `position`, the estimate factors and nulls, the threshold source, compare with one
  code, the routes and MCP, and OpenAPI drift.
- Vitest on re-recorded real responses for NumberView, SalaryChart, the URL state and ResultList.
- Playwright views and axe at 390 and 1280 px.

**Target Platform**: unchanged (`lonekrav-serve`, and the container).

**Project Type**: a web service plus its single-page client.

**Performance Goals**: "Your number" adds no request beyond today's per code: the salary, the
eligibility, one compare and the market behind an expander. The position is computed in
microseconds inside the eligibility answer.

**Constraints**:
- No interpolated percentile (FR-003).
- Every estimate is marked simulated, with its formula and inputs (FR-009).
- The number is never in the address (FR-018).
- No legal literal in code or tests outside the registry; the scan covers `frontend/src`.

**Scale/Scope**: 430 codes × 7 age options × 9 area options. Each estimate is computed per request
from data already in memory.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|---|---|---|
| I. Core first, adapters thin | `position` and the estimate live in `core/salary.py`. `Service.eligibility` attaches the position. REST and MCP only pass `region`. | Pass |
| II. Data integrity | Positions copy published values only. The estimate carries `is_simulated`, its formula, its inputs and the factors left out. Suppressed inputs leave a factor out instead of being filled. Nothing new needs `data-dict.yaml`. | Pass |
| II. Legal constants | Floors still come from the registry. Threshold lines gain their registry source. | Pass |
| III. Honest fit | Cards stay in selection order, never ranked by pay. The honest-fit statement is shown once per view. No copy suggests a code for its pay. The task descriptions stay one click away on every card. | Pass |
| IV. Test-first, proven by hand | Red/green per task. Evidence: curl of salary and eligibility, and the candidate walk screenshots at both widths. | Pass |
| V. Compact and portable | No new dependency, service or artefact. | Pass |
| VI. Simplicity | One extended model rather than a new estimate model. The chart lives in one view. The checkbox state is removed. | Pass |

Re-check after design: unchanged. The only contract widening is `/compare` accepting one code
(R4), which the spec's FR-017 requires.

## Project Structure

### Documentation (this feature)

```text
specs/006-your-number/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── http.md        # salary ?region, eligibility market_position, compare 1–5
│   ├── mcp.md         # get_occupation_salary region, eligibility position, compare 1–5
│   └── ui.md          # steps, Your number, the chart
└── tasks.md
```

### Source Code (repository root)

```text
src/lonekrav/
├── core/
│   ├── salary.py          # + position(), PercentileRef, MarketPosition; _simulate gains region;
│   │                      #   ThresholdLine.source; SalaryPayload.estimate_note
│   ├── eligibility.py     # EligibilityAnswer.market_position (field only)
│   ├── compare.py         # 1–5 codes
│   └── service.py         # salary(region=…) passes regional rows; eligibility attaches position
├── api/v1.py              # salary ?region
├── protocols/mcp_server.py        # region arg; descriptions
└── protocols/agent/loop.py        # one prompt line on positions and estimates
frontend/src/
├── App.tsx                         # numbered steps, Next buttons; OfferBox moves into NumberView
├── lib/urlState.ts                 # view number (compare → number), region, REGIONS
├── lib/selection.ts                # drop simulated
├── views/NumberView.tsx (+ test)   # NEW: replaces CompareView
├── views/CompareView.tsx (+ test)  # deleted
├── views/SearchView.tsx            # chart removed; chips + Next
├── components/SalaryChart.tsx      # redrawn (R6)
├── components/ResultList.tsx       # ScoreStrip behind <details>
├── components/OfferBox.tsx         # becomes the number input + Offer details
└── test/fixtures/*.json            # re-recorded
frontend/e2e/views.spec.ts          # view names; candidate screenshots
tests/unit/test_salary_position.py, test_salary_estimate.py (new); test_compare.py, test_salary_api.py,
test_mcp.py, test_openapi_drift.py (extended)
references/your-number.md           # evidence: curl output, screenshots, heights
```

**Structure Decision**: the existing layout. One view is replaced and nothing else new is added.

## Complexity Tracking

No violations to justify.
