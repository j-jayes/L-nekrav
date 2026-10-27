# Tasks: Your number

**Input**: Design documents from `specs/006-your-number/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: required (Constitution IV, red/green). Each test task must be seen to fail before the
task after it is implemented.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Foundational (core models)

- [X] T001 Write failing tests in `tests/unit/test_salary_payload.py` that `ThresholdLine` carries `source` equal to its rule's registry source, for every line on 2026-10-27 and on a date before June 2026 (R3)
- [X] T002 Add `source: Source` to `ThresholdLine` in `src/lonekrav/core/salary.py` and fill it in `payload()`

## Phase 2: User Story 1 — Where my number sits (P1) 🎯 MVP

**Goal**: a full-time-equivalent amount placed between published percentiles, on the eligibility answer for every surface.
**Independent test**: `POST /api/v1/eligibility` for 2511 at 60 000 gives `market_position` lower=median 56 200, upper=p75 66 700.

- [X] T003 [US1] Write failing tests in `tests/unit/test_salary_position.py` for `position()`: each of the seven brackets; exact equality gives `at`; a suppressed p25 widens to p10–median with `missing=["p25"]`; all percentiles null gives `no_data`; values are copied, never computed (property: every returned value is one of the distribution's fields)
- [X] T004 [US1] Implement `PercentileRef`, `MarketPosition` and `position()` in `src/lonekrav/core/salary.py`
- [X] T005 [US1] Write failing tests in `tests/unit/test_service.py`: `Service.eligibility` attaches `market_position` from the code's latest distribution, using salary ÷ (fte_percent/100); null for a code with no distribution; the eligibility status is unchanged by it
- [X] T006 [US1] Add `market_position` to `EligibilityAnswer` in `src/lonekrav/core/eligibility.py` and attach it in `Service.eligibility` in `src/lonekrav/core/service.py`
- [X] T007 [US1] Extend `tests/integration/test_api.py` and `tests/integration/test_mcp.py` for the field on REST and on `evaluate_permit_eligibility`; update the tool description in `src/lonekrav/protocols/mcp_server.py` (contracts/mcp.md)
- [X] T008 [US1] Write a failing test in `tests/unit/test_compare.py` that one code is accepted and six are refused with "give 1–5 distinct codes"; relax `src/lonekrav/core/compare.py` and the `compare_occupations` description (R4)

## Phase 3: User Story 2 — Estimate for age and area (P2)

**Goal**: the simulated percentiles gain an area factor, with partial estimates and reasons.
**Independent test**: `GET /salary?age_band=25-34&region=SE11` for 2511 gives p25 ≈ 44 711 and p75 ≈ 62 520 with both factors applied.

- [X] T009 [US2] Write failing tests in `tests/unit/test_salary_age.py` (or a new `test_salary_estimate.py`) for `_simulate` with a region: both factors (the 2511 numbers above); area only; age only; Sweden mean suppressed → region in `left_out` with the reason; no regional row for the year → reason names the table and year; neither applies → `simulated` null and `estimate_note` set; `formula` names only applied factors and states independence when both apply; `inputs` lists every table used; and a sweep over the committed data (every code × 7 age options × 9 area options) where each estimate equals the formula on published inputs or is absent with a reason (SC-003)
- [X] T010 [US2] Extend `SimulatedPercentiles` (`age_band` nullable, `region`, `applied`, `left_out`), `_simulate` and `payload(region=…, regional=…)` and add `SalaryPayload.estimate_note` in `src/lonekrav/core/salary.py`; validate `region` against the eight area codes
- [X] T011 [US2] Write failing tests in `tests/integration/test_api.py` and `tests/integration/test_mcp.py`: `?region=SE11` works; `?region=SE99` gives 422 listing the allowed values; the MCP tool takes `region`
- [X] T012 [US2] Pass `region` through `Service.salary` (with `self.regional`) in `src/lonekrav/core/service.py`, the route in `src/lonekrav/api/v1.py` and `get_occupation_salary` in `src/lonekrav/protocols/mcp_server.py`; add the one prompt line in `src/lonekrav/protocols/agent/loop.py` and its test in `tests/unit/test_agent_loop.py`
- [X] T013 [US2] Regenerate the schema (`uv run python scripts/export_openapi.py && (cd frontend && npm run gen)`) and confirm `tests/integration/test_openapi_drift.py` passes
- [ ] T014 [US2] Re-record the page fixtures with `scripts/record_api_fixtures.py` against a running server (salary with age and region, eligibility with a position, compare with one code), and add the new names to the script

## Phase 4: User Story 3 — A chart I can read (P2)

**Goal**: the redrawn chart (contracts/ui.md, R6).
**Independent test**: SalaryChart renders 2511 and 2512 with a number and an estimate; every mark is labelled; the scale minimum is below every drawn value and above zero.

- [ ] T015 [US3] Load the `dataviz` skill. Write failing tests in `frontend/src/components/SalaryChart.test.tsx`: the marks per row (P10–P90, P25–P75, median, estimate outline, floor), one number line across rows labelled once, no age dots, a domain padded around the drawn values, the table columns from contracts/ui.md, and the caption "Estimates are not SCB figures."
- [ ] T016 [US3] Redraw `frontend/src/components/SalaryChart.tsx` and adjust `frontend/src/lib/chartScale.ts` (padded domain, 5 000 ticks under a 30 000 span, with tests in `chartScale.test.ts`); run `validate_palette.js` if any token changes

## Phase 5: User Story 4 — Steps and Your number (P3)

**Goal**: three numbered steps; "Your number" replaces Compare.
**Independent test**: at 390×844, `/?view=number&codes=2511,2512,2519&age=25-34&region=SE11` with 60 000 typed shows the first card's position, estimate and floor check without scrolling.

- [ ] T017 [US4] Write failing tests in `frontend/src/lib/urlState.test.ts`: `view=compare` parses as `number`; `region` round-trips and invalid values are dropped; the number never appears in `serialise`
- [ ] T018 [US4] Update `frontend/src/lib/urlState.ts` (VIEWS, REGIONS with SCB's area names, region) and `frontend/src/lib/selection.ts` (drop `simulated`, with its tests)
- [ ] T019 [US4] Write failing tests in `frontend/src/views/NumberView.test.tsx` on recorded fixtures: the headline per code; the position sentence for 60 000 ("between the median and the 75th percentile"); the suppressed-bound wording; the estimate chip with "not an SCB figure" and a left-out reason; the floor check with its source; the honest-fit text and the market notice exactly once each with three codes; one code works; the empty state links to step 1; cards in selection order; an empty, zero or non-numeric number shows no position and says why while the rest renders
- [ ] T020 [US4] Implement `frontend/src/views/NumberView.tsx` (inputs; "Offer details" `<details>` reusing `OfferForm`; one card per code with `<details>` for tasks and `MarketPanel`; the chart; the legal sources). Take the notice out of `MarketPanel` into the view. Delete `frontend/src/views/CompareView.tsx` and its test
- [ ] T021 [US4] Write failing tests in `frontend/src/App.test.tsx` and `frontend/src/views/SearchView.test.tsx`: the steps nav reads "1 Find your code", "2 Your number", "3 The rules"; the Next buttons; the search view has chips and Next but no chart; the result card's ranks sit in "How this was matched"
- [ ] T022 [US4] Update `frontend/src/App.tsx`, `frontend/src/views/SearchView.tsx`, `frontend/src/components/ResultList.tsx` and `frontend/src/components/OfferBox.tsx` to pass
- [ ] T023 [US4] Update `frontend/e2e/views.spec.ts` for the `number` view and run it against `lonekrav-serve` on port 8010 at both widths (no sideways scroll, axe clean)

## Phase 6: Polish and evidence

- [ ] T024 Run the candidate walk (quickstart.md) at 390×844 and 1280×800; measure SC-001 and SC-004; write `references/your-number.md` with the curl output, the screenshots and the heights
- [ ] T025 Update `README.md` and `CLAUDE.md` ("Things worked out in Feature 006") for anything the change invalidated or taught; update the memory leftover list (the threshold source leftover is closed)
- [ ] T026 Full gates: `rtk proxy uv run pytest -q`, `(cd frontend && npm test && npm run build)`, Playwright views; then open the PR with the evidence

## Dependencies

- Phase 1 comes before everything else.
- US1 (T003–T008) and US2 (T009–T012) are independent of each other; T013–T014 need both.
- US3 needs T013. US4 needs T013 and T016.

## Parallel opportunities

T003 and T009 (different test files). T015 and T017 once T013 is done.
