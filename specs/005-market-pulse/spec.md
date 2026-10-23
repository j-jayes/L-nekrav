# Feature Specification: Market pulse

**Feature Branch**: `005-market-pulse`

**Created**: 2026-10-23

**Status**: Draft

**Input**: User description: "005-market-pulse. Show the labour market around each SSYK code next
to its salary floor: (1) live demand — the number of open ads and positions per code from
Arbetsförmedlingen's JobSearch API (jobsearch.api.jobtechdev.se/search, occupation-group = the
profile's jobtech_concept_id, limit=0, stats=region gives counts per län; probe 2026-10-23:
DJh5_yyF_hEM = 1 183 ads / 1 569 positions, 488 in Stockholms län; ads are CC0; no key needed;
stats.limit max 30), stamped with when it was fetched; codes JobTech merges (1211+1212 → 1210) say
the count is shared, and the 4 codes JobTech lacks (4430, 5322, 5324, 7619) say no count exists;
an unreachable API degrades to "unavailable", never a guessed number. (2) Regional salary — SCB
TAB5696 (2023–2025; TAB4262 for 2014–2022): average monthly salary, its 95 % CI and number of
employees per NUTS2 national area (8 areas + Sweden), all sectors, both sexes, latest year;
suppressed cells stay null; labelled as a mean, not the median the floor is based on, and the
floor stays national. Note the plan's TAB4185 is wrong: it is salaries of employees of the regions
(county healthcare employers), not geography. (3) Historical demand — yearly ad counts per code
from historical.api.jobtechdev.se (supports historical-from/to and stats=region; 2025 for
DJh5_yyF_hEM = 30 304 ads), pre-aggregated by the ETL into a committed artefact. Surfaces: REST
/api/v1, an MCP tool, the advisor may cite it, and a market panel in the page's compare view.
Honest fit: demand and regional pay are context for the code that matches the duties, never a
reason to choose a code."

## User Scenarios & Testing *(mandatory)*

Features 001–004 answer two questions for each SSYK code: what the work is, and what salary a
work permit requires. People weighing an offer also ask what the market around that code looks
like: are employers hiring for it right now, where, and what does it pay in their part of Sweden?
Feature 005 adds that context next to the floor, from two public sources. Arbetsförmedlingen
publishes every ad on Platsbanken through an open interface, coded to the occupation taxonomy.
SCB publishes average salaries per code for eight national areas.

The users are the same as in 004: a job seeker with an offer, an employer writing one, and an
adviser explaining the rules. None of this context changes which code fits a job or what the
code requires. The code must still match the duties, and the floor is the same everywhere in
Sweden.

Facts checked on 2026-10-23, which this spec relies on:
- The live ad interface is open, needs no key, and its ads are released under CC0. For one code
  it returned 1 183 open ads offering 1 569 positions, 488 of the ads in Stockholm County. It
  returns per-county counts for at most 30 values per request, which is enough for Sweden's 21
  counties plus ads with no county.
- The historical ad interface returns yearly counts per code from 2016 onwards (16 406 ads for
  the same code in 2016, 30 304 in 2025). Before 2016 it returns no coded ads.
- SCB's table of average salary by area, sector, code and sex covers 2023–2025 (an earlier table
  with the same layout covers 2014–2022). It gives the mean monthly salary, its 95 % confidence
  interval and the estimated number of employees for Sweden and its 8 national areas
  (riksområden). It has no percentiles and no county breakdown.
- The development plan names a different SCB table for regional pay. That table holds the pay
  of people employed by the regions (the county health-care authorities), not pay by area, so
  this feature does not use it.

### User Story 1 - See how many jobs are open for a code (Priority: P1)

A job seeker comparing two plausible codes for their job opens the compare view. Under each code
they see how many ads are open on Platsbanken right now, how many positions those ads offer, and
in which counties. Each count says when it was fetched and where it comes from. The panel repeats
that the code must match the duties, and that demand has no bearing on which code that is.

**Why this priority**: open demand is the one piece of market context that no other part of
Lönekrav has, and the live interface was checked to answer per code. It is useful without the
other two stories.

**Independent Test**: request the market for a code with a known JobTech concept, and check that
the counts equal what the ad interface returns for that concept at the same time, with the fetch
time and the source.

**Acceptance Scenarios**:

1. **Given** a code with a JobTech concept, **When** the market is requested, **Then** it returns
   the number of open ads, the number of positions, and the ads per county, with the fetch time
   and the source, and these equal what the ad interface reports for that concept.
2. **Given** a code that JobTech merges with others (for example 1211 and 1212, which JobTech
   publishes as one group), **When** the market is requested, **Then** the counts are those of the
   merged group, and the answer names every code that shares them.
3. **Given** one of the four codes JobTech does not publish (4430, 5322, 5324, 7619), **When** the
   market is requested, **Then** it says that no count exists for that code, and shows no number.
4. **Given** the ad interface cannot be reached or answers with an error, **When** the market is
   requested, **Then** the answer says the live count is unavailable and why, the rest of the
   page and API keep working, and no number is shown.
5. **Given** the same code is requested twice within a short time, **When** the second answer is
   returned, **Then** it reuses the first count, with its original fetch time.

---

### User Story 2 - See what a code pays in each part of Sweden (Priority: P2)

An employer in Västsverige wants to know how the offer compares with what the code pays locally.
Next to the national floor, they see SCB's average monthly salary for the code in each of the
eight national areas and for Sweden as a whole, with each mean's confidence interval and the
number of employees behind it, for the latest year. The panel states that these are means, while
the floor is based on the national median, and that the floor is the same in every area.

**Why this priority**: regional pay is context for negotiation, not for eligibility. The data is
annual and stable, so it can be built ahead of time, but it is less new than live demand.

**Independent Test**: build the regional table from a fixture slice of SCB's table and check that
every published figure for a code matches the slice, and that a suppressed cell stays empty.

**Acceptance Scenarios**:

1. **Given** a code with published regional figures, **When** its regional pay is requested,
   **Then** it returns, for Sweden and each of the 8 areas, the mean monthly salary, its 95 %
   confidence interval and the number of employees, for the latest year, with the SCB table and
   reference year.
2. **Given** an area where SCB suppressed a figure, **When** regional pay is shown, **Then** that
   figure is empty and marked as not published, never filled from another area or year.
3. **Given** the page shows regional pay beside the floor, **When** a user reads it, **Then** the
   panel says the figures are means, that the floor comes from the national median, and that the
   floor does not vary by area.

---

### User Story 3 - See how demand for a code has changed over the years (Priority: P3)

An adviser explaining a field to a client wants to show whether hiring for the code has grown or
shrunk. For each code they see the number of ads published on Platsbanken in each full year since
2016, as a small chart with a table view, with the source and the date the counts were built.

**Why this priority**: a trend gives the live count a scale, but it is the least urgent of the
three, and it needs one ahead-of-time pass over all codes.

**Independent Test**: build the yearly counts for a fixture set of codes and check each year
against the historical interface's answer recorded in the fixture.

**Acceptance Scenarios**:

1. **Given** a code with a JobTech concept, **When** its history is requested, **Then** it returns
   the number of ads published in each full year from 2016 to the last full year, with the source
   and the build date.
2. **Given** a year with no ads for the code, **When** history is shown, **Then** that year shows
   zero, which is a real count, and is not confused with a missing year.
3. **Given** a code JobTech merges or lacks, **When** history is requested, **Then** it is labelled
   in the same way as the live count (shared with named codes, or no count exists).

---

### User Story 4 - Ask the advisor and other tools about the market (Priority: P3)

A user asks a chat assistant connected to Lönekrav how many jobs are open for a code. The
assistant gets the same answer as the page. The advisor may cite the live count and regional pay
in its memo, with their sources, and never uses them to suggest a different code.

**Why this priority**: the machine interfaces already share one core, so this follows from
stories 1–3 at low cost.

**Independent Test**: call the market tool through each machine interface for a code, and check
that the answer equals the REST answer; check the advisor's memo against the honest-fit rules on
a recorded run.

**Acceptance Scenarios**:

1. **Given** a code, **When** the market is requested through REST and through the chat-tool
   interface, **Then** both return the same counts, regional figures, history and labels.
2. **Given** the advisor writes a memo that mentions demand or regional pay, **When** the memo is
   checked, **Then** each figure names its source and time, and no sentence suggests choosing a
   code because of demand or pay.

---

### Edge Cases

- The ad interface is slow: the market answer stops waiting after a short limit and says the live
  count is unavailable, rather than holding up the page.
- The ad interface returns a count with no county for some ads: those ads appear as "no county
  given", so the county counts add up to the total.
- One ad can offer several positions, so positions can exceed ads; both are shown and labelled.
- A code has open ads but zero in most counties: only counties with ads are listed, in order of
  count, and the total is unchanged.
- A code's regional figures are all suppressed except Sweden's: the national mean is shown and the
  areas are each marked as not published.
- The latest SCB year is newer than the year of the national median the floor uses: each figure
  shows its own reference year, and nothing is rescaled to match.
- The current year is partial: history shows full years only, so a half year never looks like a
  drop.
- A code that JobTech merges into a group is compared with another member of the same group: both
  columns show the same shared count, each saying it is shared.

## Requirements *(mandatory)*

### Functional Requirements

**Live demand**

- **FR-001**: The system MUST return, for a code, the number of open ads, the number of positions
  they offer, and the ads per county, as reported by Arbetsförmedlingen's live ad interface for
  the code's JobTech concept.
- **FR-002**: Every live count MUST carry its source, the concept it was fetched for, and the time
  it was fetched.
- **FR-003**: For a code that JobTech merges into a group, the count MUST be the group's count and
  MUST name every code in that group.
- **FR-004**: For a code JobTech does not publish, the answer MUST say that no count exists and
  carry no number.
- **FR-005**: When the live interface cannot be reached, answers with an error, or does not answer
  within the time limit, the answer MUST say the live count is unavailable, with the reason, and
  carry no number. No count may be estimated, carried over from history or taken from another
  code.
- **FR-006**: A live count MUST be reused for repeat requests for the same concept for a short
  period, keeping its original fetch time, so that a page of four codes does not make the
  interface answer the same question repeatedly.
- **FR-007**: The default test run MUST NOT contact the live interface; a live check MUST exist
  that is skipped when the network is unavailable.

**Regional pay**

- **FR-008**: The system MUST provide, for each code, SCB's mean monthly salary, its 95 %
  confidence interval and the estimated number of employees for Sweden and each of the 8 national
  areas, for all sectors and both sexes, for the latest published year.
- **FR-009**: Every regional figure MUST carry the SCB table, the reference year and the fetch
  time. A figure SCB does not publish MUST stay empty and be marked as not published.
- **FR-010**: Wherever regional pay is shown, the system MUST state that the figures are means,
  that the salary floor is based on the national median, and that the floor is the same in every
  area. Regional pay MUST NOT be drawn as, or compared to, a threshold.
- **FR-011**: The regional table MUST be built ahead of time by the data pipeline, committed with
  the other processed data, and recorded in the data dictionary with its provenance, licence and
  credit.

**Historical demand**

- **FR-012**: The system MUST provide, for each code with a JobTech concept, the number of ads
  published in each full calendar year from 2016 to the last full year before the build.
- **FR-013**: Yearly counts MUST be built ahead of time by the data pipeline, committed with the
  other processed data, recorded in the data dictionary, and carry the source and the build date.
- **FR-014**: A year with no ads MUST be stored and shown as zero; a year the pipeline could not
  fetch MUST fail the build rather than be stored as zero or left out.

**Surfaces**

- **FR-015**: The REST interface MUST offer the market for a code: live demand, regional pay and
  history in one answer, each part with its own status.
- **FR-016**: The chat-tool interface MUST offer the same answer as a tool, through the same core
  function as REST.
- **FR-017**: The advisor MAY cite the live count and regional pay in its memo. Each cited figure
  MUST name its source and time, and the advisor's instructions MUST forbid using demand or pay as
  a reason to choose a code.
- **FR-018**: The page's compare view MUST show a market panel for each selected code: the live
  counts with the top counties, the regional means beside the national floor, and the yearly
  history as a small chart with a table view. Each part shows its source, time and status.
- **FR-019**: The market panel MUST state that the code has to match the actual duties, and that
  demand and regional pay are context, not a reason to choose a code.
- **FR-020**: The panel MUST work at 390 px wide with no sideways scroll and pass the automated
  accessibility check, as the 004 views do.

### Key Entities

- **Live demand**: for one JobTech concept at one time, the open ads, the positions and the ads
  per county; its source, concept, fetch time, status (available, shared, no count, unavailable)
  and the codes that share it.
- **Regional pay row**: for one code, one area and one year, the mean monthly salary, the margin
  of its 95 % confidence interval (SCB publishes it as one ± figure), and the number of employees,
  each possibly empty; with the SCB table and fetch time.
- **Yearly demand**: for one JobTech concept and one full year, the number of ads published; with
  the source and the build date.
- **Market answer**: for one code, the three parts above, each with its own status, plus the
  honest-fit statement.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For 10 sampled codes, the live open-ad count equals the ad interface's own count for
  the same concept fetched in the same minute.
- **SC-002**: The market answer for a code, including a live fetch, arrives within 2 seconds on
  the reference machine, and within 0.1 seconds when the live count is reused.
- **SC-003**: With the ad interface unreachable, every market answer arrives within 5 seconds and
  says the live count is unavailable, and every other route still answers.
- **SC-004**: 100 % of the regional figures served for a fixture slice match SCB's published
  cells, and 100 % of suppressed cells are served as empty.
- **SC-005**: For every code in the processed data, the yearly history has one count for each
  full year from 2016 on, or is labelled as no count.
- **SC-006**: The compare view with the market panel shows no sideways scroll at 390 px and
  1280 px, with screenshots, and has no serious or critical accessibility violations.
- **SC-007**: No copy, tool description or advisor memo produced in the feature's tests suggests
  choosing a code because of demand or pay, as checked by the existing honest-fit wording tests.

## Assumptions

- The reference machine is the maintainer's laptop (Apple M2 Pro, 16 GB), as in Features 001–004.
- The live ad interface stays open without a key, as it was on 2026-10-23. If it later requires
  a key, the key would live in `.env` and the live count would degrade to unavailable without it.
- Ads are counted by their JobTech occupation-group concept, which is the same concept the
  profiles already store for each code. An ad coded only to a broader level is not counted under
  any 4-digit code.
- The reuse period for a live count is 15 minutes; Platsbanken changes over hours, not seconds.
- The latest SCB year for regional pay is 2025. The earlier table (2014–2022) is not needed for
  the latest-year view and is out of scope.
- Regional pay uses SCB's national areas because that is the finest geography SCB publishes per
  4-digit code; county pay is not available and is out of scope. Live ad counts use counties,
  because that is what the ad interface reports. The two are shown separately, not joined.
- History counts ads, not positions, because the historical interface does not report positions
  reliably (it returned zero positions for a year with ads in one probe).
- Market context is shown in the compare view only, not on the search results, so as not to
  slow the search or invite choosing a code by demand.
- SCB's regional table is open data under CC0, like the other SCB tables in Lönekrav, and carries
  the same Medlingsinstitutet credit.
