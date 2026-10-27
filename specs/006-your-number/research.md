# Research: Your number

All decisions below were checked against the code and the committed data on 2026-10-27.

## R1. Where the market position is computed

- **Decision**: a pure function `core.salary.position(amount, distribution)`. It is served as a new
  field, `market_position`, on the existing eligibility answer (`POST /api/v1/eligibility` and the
  MCP tool `evaluate_permit_eligibility`). `Service.eligibility` attaches it after `evaluate`, from
  the code's latest distribution. The amount is the full-time equivalent: salary ÷ share of full
  time, the same convention the floor check uses.
- **Rationale**: Principle I puts domain logic in core and serves it to every surface. The
  eligibility request already carries the candidate's salary in a POST body, so the number goes to
  the server no differently than it does today. It is never in a URL, so it never lands in a server
  log or the page address (FR-018). The advisor gets the position through the tool it already
  calls.
- **Alternatives**: a `?amount=` query on `GET /salary` was rejected because it puts the number in
  URLs and access logs. Computing the position only in TypeScript was rejected because it
  duplicates domain logic and the MCP surface would lack it.

## R2. The estimate: extend the existing age simulation

- **Decision**: extend `core.salary._simulate` and `SimulatedPercentiles` with an optional `region`.
  - The factors are the age factor (band mean ÷ all-ages mean, TAB5844) and the area factor
    (area mean ÷ Sweden mean, TAB5696), all for the distribution's year.
  - Each factor is applied when its inputs are published and listed in `left_out` with a reason
    when they are not.
  - `formula` names only the factors applied, and states the multiplication assumption when both
    are applied.
  - `inputs` lists every table used.
  - All five percentiles stay simulated, as today. The page shows P25–P75 as the band, and the
    table shows the rest.
- **Rationale**: the age simulation already carries `is_simulated`, its formula and its inputs
  (Principle II), and the page and the advisor already read it. One model serves both factors.
- **Data check (2025)**: TAB5696's Sweden row is missing for 34 codes and Stockholm for 96; 926 of
  3 010 age cells are suppressed. Partial estimates (one factor) are therefore common and must be
  first-class (FR-010).
- **Year rule**: regional data covers 2023–2025 and the percentiles 2014–2025. The estimate uses the
  distribution's year for every input. A factor whose table has no row for that year is left out
  with the reason "no {table} figures for {year}".
- **Alternatives**: a separate `Estimate` model was rejected because it would mean two simulated
  shapes for the same idea. Scaling only P25 and P75 was rejected because it is less general and
  the existing shape already has all five.

## R3. The threshold line names its legal source

- **Decision**: add `source: Source` (the rule's registry source) to `core.salary.ThresholdLine`.
- **Rationale**: this closes the tracked leftover from 005, where advisor memos said the salary
  payload's 90 %/75 % lines have no citation. It is required by FR-006 and costs one field.

## R4. "Your number" with one code: relax compare to 1–5 codes

- **Decision**: `core.compare` accepts 1–5 distinct codes, down from 2–5. "Your number" calls
  `/compare` for the honest-fit text, the tasks and the eligibility of each code.
- **Rationale**: FR-017 needs the view to work with one code. The compare column already holds the
  task selection logic (MIS first, then JobTech; ESCO for English), so reusing it avoids duplicating
  that logic. One code is a valid "comparison" of one plausible code.
- **Contract impact**: the REST `POST /compare` and the MCP `compare_occupations` description change
  from "2–5" to "1–5". The test of the old error message changes with them.

## R5. Page structure

- **Decision**:
  - The views are `search` (1 Find your code), `number` (2 Your number) and `legal` (3 The rules).
    `?view=compare` parses as `number`.
  - The address gains `region` (`SE11`…`SE33`), validated against a constant list like `AGE_BANDS`.
  - The salary chart moves from the search view to "Your number". The search view keeps the
    selected-code chips and a "Next: your number" button.
  - The offer box becomes a "Your number" input plus an "Offer details" `<details>` that reuses
    `OfferForm`. Its defaults are `emptyDraft()`: full time, first permit, filed and decided today.
  - The per-code "simulated" checkboxes and the `simulated` selection action are removed.
- **Rationale**: one chart in one place, and it sits where the number is. Removing the checkbox
  state shrinks the reducer.
- **Alternative**: keeping the chart on both views was rejected because it would show two copies of
  the same chart with different marks.

## R6. The chart scale and marks

- **Decision**: the domain is [min(P10, floor, number, estimate low) − pad, max(P90, number,
  estimate high) + pad], with `pad` one tick step and ticks every 10 000 SEK (5 000 when the span is
  under 30 000). Load the `dataviz` skill before drawing and run its `validate_palette.js` on any
  new token.
  - P10–P90 is drawn in `--color-band` (light).
  - P25–P75 is drawn in `--color-bar`.
  - The median is a tick in `--color-ink`.
  - The candidate's number is a line in `--color-dot` (accent orange), labelled once.
  - The floor is a dashed line in `--color-muted`, labelled "floor".
  - The estimate is a dashed outline.
- **Rationale**: the eye should go to the middle half of the market and the candidate's number,
  not to the floor or the low-pay end (review finding 3). Existing tokens are reused; no palette
  change is planned.

## R7. Correction to the review

A scripted walk first suggested that "Add to chart" failed while the accurate search refined. A
re-check (`scratchpad/refine.mjs`) showed the script matched the button by the wrong name ("Add to
chart", not "Add 2519 to chart"), and that adding works. The finding was dropped from the spec.
The slow first accurate search was real: 11.4 s cold on 2026-10-27, against 3.3 s warm by curl.
It is left as is: it is a search latency matter, which 006 does not touch.
