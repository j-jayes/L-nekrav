# Feature Specification: Your number

**Feature Branch**: `006-your-number`

**Created**: 2026-10-27

**Status**: Draft

**Input**: User description: "Feature 006 'Your number'. A full frontend review from the point of
view of a work-permit applicant invited to a final-round interview, who needs to know what salary
to ask for. The figure must clear two bars: the legal salary floor (a gate) and the occupation's
market (the target). The page today has a lot of information but not the right framing. Lead with
the market; show where the candidate's number falls among SCB's published figures; give an
age- and region-adjusted estimate that is clearly labelled as not an SCB figure; keep the floor as
a pass/fail check under it. Restructure the page as numbered steps (Find your code → Your number →
The rules). The occupation map is Feature 007 and out of scope here."

## User Scenarios & Testing *(mandatory)*

Features 001–005 answer: which SSYK code fits a job, what floor a work permit requires for it, and
what the market around it looks like. A walk through the page on 2026-10-27, as a candidate
preparing a salary ask for a data-science role, found that it never answers the candidate's own
question: *what number should I ask for?*

- The headline of the salary view is the floor. For code 2511 the floor is 34 470 SEK and the
  median 56 200 SEK, so the floor says nothing about a sensible ask; it only rules out very low ones.
- SCB's 75th percentile reaches the page and is never shown. The candidate's own figure is never
  drawn; an offer is only checked against the floor.
- The age-band means are unlabelled dots, and the age-band choice does nothing until a per-code
  "simulated" box is ticked. Regional pay appears only as a dense table at the end of the compare
  view.
- The compare view is about 2 200 px tall on a desktop screen: full task descriptions, the market
  notice repeated once per code, a regional table per code, and the one line the candidate needs
  ("Median 56 200 SEK; P10–P90 …") buried near the top of each column.
- Search results show the engine's internals ("Swedish model #1 · Keywords #4 · Accurate model
  not run"). (A scripted run first suggested that "Add to chart" failed while results refined; a
  re-check showed the script used the wrong button name, and adding works.)

The user is a work-permit applicant (or someone advising one) who has, or expects, an offer. Their
figure must clear two bars: the legal floor, which is a gate the permit cannot pass without, and
the market for the work, which is what the employer will compare it with. The code must still
match the actual duties; this feature changes how pay is shown, never which code is suggested.

Facts checked on 2026-10-27, which this spec relies on:
- SCB publishes percentiles (P10, P25, median, P75, P90) per code nationally, for all ages, both
  sexes and all sectors together. In the latest year (2025), P25 is missing for 46 of 430 rows and
  P75 for 37.
- SCB publishes mean monthly salary per code for six age bands and for all ages (2025: 926 of
  3 010 age cells are suppressed), and per code for Sweden and eight national areas (2025: 1 315 of
  3 870 cells suppressed; the Sweden row is missing for 34 codes, Stockholm for 96).
- Example, code 2511 in 2025: P10 41 000, P25 47 700, median 56 200, P75 66 700, P90 77 800 SEK;
  mean 58 500 for all ages, 50 200 for ages 25–34; mean 58 500 in Sweden, 63 900 in Stockholm.
- Lönekrav already derives age-adjusted percentiles by scaling SCB's percentiles by an age band's
  mean relative to the all-ages mean, marked as simulated with its formula.

### User Story 1 - See where my number sits (Priority: P1)

A candidate has chosen the code that matches their duties and types the monthly salary they plan
to ask for. They immediately see SCB's published P25, median and P75 for the code, a sentence that
places their number among them ("Your 60 000 SEK is between the median and the 75th percentile"),
and whether it clears the work-permit floor and by how much. They can do this for each selected
code side by side.

**Why this priority**: it answers the question the candidate came with, using only published
figures. It is useful on its own, without estimates or the new layout.

**Independent Test**: select 2511, type 60 000; check the published P25, median and P75 equal
SCB's 2025 values, the bracket reads "between the median and the 75th percentile", and the floor
check reports a pass with the margin from the eligibility rules.

**Acceptance Scenarios**:

1. **Given** code 2511 is selected and the candidate types 60 000, **When** the view updates,
   **Then** it shows P25 47 700, median 56 200 and P75 66 700 SEK with their SCB table and year,
   states that 60 000 is between the median and the 75th percentile, and reports that it clears
   the floor with the margin in SEK and per cent.
2. **Given** the number is below the code's P10, **When** the view updates, **Then** it says the
   number is below the 10th percentile; above P90, it says above the 90th percentile. No percentile
   value between published points is ever stated.
3. **Given** a code whose P25 (or another bound needed for the bracket) is suppressed by SCB,
   **When** the number falls where that bound matters, **Then** the bracket names the nearest
   published bounds it can (for example "between the 10th percentile and the median") and says
   which figure SCB does not publish; it never fills the gap.
4. **Given** a number below the floor, **When** the view updates, **Then** the floor check fails
   visibly with the shortfall, independent of where the number sits in the market.
5. **Given** a code for which permits cannot be granted, **When** the view updates, **Then** it
   says so instead of a floor check, and still shows the market position.

---

### User Story 2 - An estimate for my age and region (Priority: P2)

The candidate picks their age band and the national area where the job is. Each code shows an
estimated range for people like them, built from SCB's national P25–P75 scaled by how the age
band's and the area's mean pay compare with the national all-ages mean. The range is visibly
different from published figures, is labelled "estimate, not an SCB figure", and opens to show the
formula, its inputs (tables and years) and the assumption that the two adjustments combine by
multiplication.

**Why this priority**: national figures mix 25-year-olds in Upper Norrland with 50-year-olds in
Stockholm; the estimate narrows that, but it is derived, so it comes second to the published facts.

**Independent Test**: select 2511, age 25–34, Stockholm; check the range equals P25 and P75 times
(50 200 / 58 500) × (63 900 / 58 500), about 44 700–62 500 SEK, rounded as the existing simulated
figures are, and that it is marked simulated with formula and inputs.

**Acceptance Scenarios**:

1. **Given** a code, an age band and an area with all inputs published, **When** the view
   updates, **Then** the estimate range is shown with both adjustments named, marked as an
   estimate, and its formula and source tables are one step away.
2. **Given** the area's mean or the Sweden mean is suppressed for that code, **When** the view
   updates, **Then** the estimate applies only the age adjustment and says the area adjustment
   could not be applied because SCB does not publish it; likewise for a suppressed age-band mean.
3. **Given** neither adjustment can be applied, or P25 and P75 are both suppressed, **When** the
   view updates, **Then** no estimate is shown and the reason is stated.
4. **Given** no age band or area is chosen, **When** the view updates, **Then** no estimate is
   shown and the published figures stand alone.
5. **Given** the candidate's number, **When** an estimate exists, **Then** the position sentence
   still refers to the published percentiles; the estimate is never used to place the number.

---

### User Story 3 - A chart I can read at a glance (Priority: P2)

The salary chart shows, per selected code, the published P10–P90 spread with the P25–P75 middle
half emphasised and the median marked; the candidate's number as one labelled line across all
rows; the floor as a muted labelled line; and the estimate range as a dashed outline labelled
"estimate". The scale starts near the lowest value drawn rather than at zero. A table view gives
the same numbers, including P75, the estimate and the candidate's number.

**Why this priority**: the chart is where the eye goes; today it emphasises the floor and the
low-pay end, and its age dots cannot be read.

**Independent Test**: render the chart for 2511 and 2512 with a number and an estimate; check each
mark's position against its value, each mark is labelled, the scale minimum lies below every drawn
value and above zero, and the table lists every drawn value.

**Acceptance Scenarios**:

1. **Given** codes, a number and an estimate, **When** the chart renders, **Then** every mark has
   a visible label or legend entry, and focusing or tapping any mark reads out its value and source.
2. **Given** no number is entered, **When** the chart renders, **Then** no number line appears and
   the chart invites the candidate to enter one.
3. **Given** a phone-width screen (390 px), **When** the chart renders, **Then** there is no
   sideways scrolling and labels keep their size.
4. **Given** a code with no published percentiles, **When** the chart renders, **Then** its row
   says SCB publishes no figures for it and draws nothing invented.

---

### User Story 4 - A page that walks me through it (Priority: P3)

The page reads as three numbered steps: 1 Find your code, 2 Your number, 3 The rules. Each step
ends with a button to the next. "Your number" replaces the compare view: it leads with the number,
the position and the floor check per code; task descriptions, open ads, regional pay and ads per
year sit behind expandable sections. The honest-fit statement and the market notice appear once
per view, not once per code. Search results lead with the title and matched passage; how each
search method ranked the code is one step away.

**Why this priority**: it makes stories 1–3 easy to find and removes the wall of text, but the
numbers are what matter.

**Independent Test**: on a 390 × 844 screen, open "Your number" for 2511, 2512 and 2519 with a
number, age band and area chosen; the first code's position sentence, estimate and floor check are
visible without scrolling.

**Acceptance Scenarios**:

1. **Given** a link that names the old compare view, **When** it is opened, **Then** the page
   shows "Your number" with the same codes.
2. **Given** codes, age band and area are chosen, **When** the address is copied and opened
   elsewhere, **Then** the same codes, age band and area are restored, and the candidate's number
   is not (it is never put in the address).
3. **Given** "Your number" with three codes, **When** it renders, **Then** the honest-fit statement
   and the market notice each appear exactly once.
4. **Given** one selected code, **When** "Your number" opens, **Then** it shows that code's figures
   (comparison is no longer required to see a number).

---

### Edge Cases

- The number equals a published percentile exactly: it is described as "at the median" (or the
  relevant percentile), not as inside a bracket.
- The number is entered for part-time work: the floor check uses the existing full-time rules and
  their warning; the market position compares the full-time-equivalent figure and says so.
- The age band has a mean but the all-ages mean is suppressed: the age adjustment cannot be applied.
- The latest regional year differs from the latest percentile year: the estimate uses the same
  year for every input or is not shown.
- A code with exempt or partial-ban flags: the floor check follows the existing eligibility rules;
  the market position is shown as for any code.
- An invalid number (empty, zero, negative, non-numeric): no position is shown and the input says
  why; the rest of the view still renders.
- The advisor selects codes while the candidate is on "Your number": the view updates as the chart
  does today.

## Requirements *(mandatory)*

### Functional Requirements

**The candidate's number and its position**

- **FR-001**: Users MUST be able to enter one monthly salary figure (their number) on "Your
  number"; it is the same figure the floor check uses as the offer, entered once. The other offer
  details the floor check needs (share of full time, application type, dates, exemptions) default
  to full time and a first permit filed and decided today, and can be changed in an expandable
  "Offer details" section.
- **FR-002**: For each selected code the system MUST show SCB's published P25, median and P75 for
  the latest year, with table and reference year; P10 and P90 MUST be available in the chart and
  table.
- **FR-003**: The system MUST place the number in a bracket between adjacent published
  percentiles (below P10, P10–P25, P25–median, median–P75, P75–P90, above P90, or exactly at one),
  and MUST NOT state any interpolated percentile.
- **FR-004**: Where a bracket bound is suppressed, the system MUST widen the bracket to the nearest
  published bounds and name the missing figure; with no published percentiles it MUST say no
  position can be given.
- **FR-005**: The floor check MUST be shown under the market position for each code, with pass or
  fail and the margin, using the existing eligibility rules and legal registry only.
- **FR-006**: Every floor shown MUST link its legal source and show its checked-on date (this
  closes the tracked leftover that the threshold lines in the salary answer carry no source).

**The estimate**

- **FR-007**: Users MUST be able to choose an age band (SCB's six bands) and a national area
  (Sweden's eight national areas, or none).
- **FR-008**: The system MUST compute the estimate as the published P25 and P75 multiplied by the
  age factor (age-band mean ÷ all-ages mean) and the area factor (area mean ÷ Sweden mean), all from
  the same reference year, rounded as existing simulated figures are.
- **FR-009**: The estimate MUST be marked as simulated, carry its formula (stating that the two
  factors are assumed to combine by multiplication) and list every SCB table and year used, and
  MUST be visually distinct from published figures wherever it appears.
- **FR-010**: If one factor's inputs are suppressed, the estimate MUST apply only the other and say
  which adjustment was left out and why; if neither applies, or P25 and P75 are both missing, no
  estimate is shown and the reason is stated. A missing P25 or P75 alone gives a one-sided estimate
  only for the published bound.
- **FR-011**: The area choice and age band MUST be available to every surface that already serves
  salary answers (the REST interface and the MCP tool), with the same estimate and the same labels.

**The chart**

- **FR-012**: The chart MUST draw, per code: P10–P90 as a neutral bar, P25–P75 emphasised, the
  median as a tick, the estimate as a dashed outline labelled "estimate", the floor as a muted
  dashed line labelled "floor", and the candidate's number as one labelled accent line across rows.
- **FR-013**: The chart's scale MUST start just below the lowest drawn value (not at zero) and end
  just above the highest, with tick labels that stay legible at 390 px width.
- **FR-014**: The age-band mean dots and the per-code "simulated" checkbox MUST be removed; the
  estimate replaces them.
- **FR-015**: The chart MUST keep its accessible table view, adding P75, the estimate and the
  number, and keep its source caption and Medlingsinstitutet credit.

**The page**

- **FR-016**: The views MUST be presented as numbered steps — 1 Find your code, 2 Your number,
  3 The rules — each ending with a control to go to the next step.
- **FR-017**: "Your number" MUST replace the compare view and work with one to four codes; an
  address naming the compare view MUST open "Your number".
- **FR-018**: Codes, view, age band and area MUST be kept in the address; the number, offer, ad and
  background MUST NOT be.
- **FR-019**: On "Your number", task descriptions, open ads, regional pay and ads per year MUST sit
  behind expandable sections per code; the honest-fit statement and the market notice MUST appear
  once per view.
- **FR-020**: Search result cards MUST lead with code, titles and the matched passage; the per-
  method ranks MUST move behind a "How this was matched" section.
- **FR-021**: Copy MUST NOT suggest choosing a code for its pay or floor; the existing honest-fit
  wording stays, and nothing on "Your number" ranks codes by pay.

### Key Entities

- **Candidate's number**: a monthly salary in SEK and a share of full time; held only in the page,
  never in the address or on the server beyond a single request.
- **Market position**: for one code and one number — the bracket (lower and upper published
  percentile names and values, either may be open), whether the number equals a percentile, and the
  names of any suppressed bounds.
- **Salary estimate**: for one code, age band and area — low and high values (either may be null),
  the factors applied and left out with reasons, the formula, the input tables and years, and the
  simulated mark.
- **National area**: one of SCB's eight national areas (riksområden) plus Sweden, as already
  published in the regional salary data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a 390 × 844 screen, with three codes, a number, an age band and an area chosen,
  the first code's position sentence, estimate and floor check are visible without scrolling.
- **SC-002**: For every code in the latest year, the position given for 100 sample numbers matches
  the published percentiles exactly, and no displayed position contains a percentile value SCB
  does not publish.
- **SC-003**: For every code, age band and area, the estimate either equals the formula applied to
  published inputs or is absent with a stated reason; no estimate is ever shown without its
  simulated mark.
- **SC-004**: "Your number" for three codes is at most half the height of today's compare view for
  the same codes on a desktop screen (today about 2 200 px).
- **SC-005**: Every view keeps zero serious accessibility violations and no sideways scrolling at
  phone and desktop widths.
- **SC-006**: A candidate who has never used the page can, from a link with a code preselected,
  read off where their number sits and whether it clears the floor in under one minute.

## Assumptions

- The floor, its percentages and dates come only from the existing legal registry; nothing here
  changes eligibility logic.
- Age and area adjustments use means because SCB publishes no percentiles by age or area; scaling
  percentiles by a ratio of means is a stated approximation, as for the existing age simulation.
- The national areas are the eight already in the regional salary data; county-level pay is not
  published by SCB and is out of scope.
- Sector, sex and experience are not available as percentile splits in the data Lönekrav holds and
  are out of scope; age stands in for experience and is labelled as age.
- The advisor keeps working as today; it may cite the estimate through the same salary tool, with
  the same simulated labels.
- The occupation similarity map and neighbour lists are Feature 007.
- Part-time numbers are compared with the market as full-time equivalents, the same convention the
  floor check already uses.
