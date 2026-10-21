# Feature Specification: Occupation Search, Permit Eligibility and Salary API

**Feature Branch**: `002-search-eligibility-api`

**Created**: 2026-10-21

**Status**: Draft

**Input**: User description: "002-search-eligibility-api: Search, eligibility and salary API for
Swedish work permits, built on the Feature 001 occupation index. (1) Job-ad parsing: split a pasted
ad into duties, skills, company blurb and benefits, keeping only the parts that describe the job for
search. (2) Two-speed search: a fast path (KBLab dense + BM25, ~50 ms budget) and a full path that
adds Harrier, including the open Swedish search quality gates from 001 — diagnose first whether the
gap comes from the query sets before tuning models. (3) Eligibility logic in a LegalConstants
registry: 90 % or 75 % threshold, extensions filed 1 Jun–1 Dec 2026 keep the 80 % rule, banned codes,
part-time warning, stale-data warning. (4) Salary payloads naming SCB table and year; age-adjusted
figures flagged is_simulated. (5) Compare 2–5 codes side by side. (6) Versioned web API. Framing is
honest fit. Anything needing the OpenRouter key must be skippable without it."

## Clarifications

### Session 2026-10-21

- Q: Must the benchmark gates pass in fast mode too, or only in full mode? → A: Full mode passes
  every gate; fast mode must reach ≥ 80 % top-five recall in each language.
- Q: If the Swedish gap comes mostly from slash-joined queries, how is it fixed? → A: Search treats
  "/" as alternatives (searches each part and merges the results); the benchmark queries stay
  unchanged.
- Q: Should an ad's job title be kept for search as its own kind of passage? → A: Yes: a "title"
  label, always kept.
- Q: May the service keep the ads, salaries and other details users send it? → A: Request contents
  may be logged for debugging and are deleted after a short period (set to 7 days).

## User Scenarios & Testing *(mandatory)*

The people this feature serves are non-EU job seekers, and the people advising them, who hold a job
offer or a job ad and need to know which SSYK 2012 occupation codes plausibly describe the job and
what salary each code requires for a Swedish work permit. They mostly write in English, sometimes in
Swedish. The direct consumers are the later Lönekrav surfaces (MCP and A2A in 003, the web client in
004), which call this feature's operations and must get the same answers.

### User Story 1 - Check whether an offer meets the salary requirement (Priority: P1)

A user enters an SSYK code, the offered monthly salary, the share of full time, the application
type (first permit or extension), the date the application is filed and, for extensions, the date
the current permit was granted, plus any personal exemption that applies (start-up employer, former
student, licensed profession, temporary protection). They get back which rule applies, the threshold
in kronor, whether the offer passes, by how much, and every warning that matters, each with its
legal source and the date that source was checked.

**Why this priority**: The salary threshold is the question every user is trying to answer. It is
pure rules over published figures, so it can ship and be trusted before search is perfect.

**Independent Test**: Call the eligibility operation with the boundary cases listed below and compare
each answer with Migrationsverket's published amounts and SFS 2026:605 by hand.

**Acceptance Scenarios**:

1. **Given** a first-permit application filed on 16 June 2026 for code 2512 at 40 000 SEK full
   time, **When** eligibility is evaluated, **Then** the 90 % rule applies, the threshold is
   34 470 SEK (90 % of the 38 300 median), the offer passes with a margin of 5 530 SEK, and the
   answer cites the rule's source and the SCB reference year of the median.
2. **Given** the same application filed on 15 June 2026, **When** eligibility is evaluated,
   **Then** the median in force that day (37 100, published June 2025) is used and the threshold is
   33 390 SEK.
3. **Given** a first-permit application for code 3511 (exempt), **When** eligibility is evaluated
   on or after 16 June 2026, **Then** the 75 % level applies and the threshold is 28 725 SEK.
4. **Given** an application for code 5343, **When** eligibility is evaluated, **Then** the answer
   is "not permitted" whatever the salary, citing the ban, and no pass/fail on salary is shown as if
   it mattered.
5. **Given** code 9210, **When** eligibility is evaluated, **Then** the answer warns that permits
   are banned for forest berry pickers in this code and applies the 75 % level otherwise.
6. **Given** an extension filed on 30 November 2026 for a permit granted before 1 June 2026,
   **When** eligibility is evaluated, **Then** the transitional 80 % rule applies; **Given** the same
   extension filed on 2 December 2026, **Then** the 90 % rule applies.
7. **Given** an offer of 40 000 SEK at 80 % of full time, **When** eligibility is evaluated, **Then**
   the threshold is not reduced for part-time and the answer carries a part-time warning that says
   so in plain words.
8. **Given** an evaluation date after mid-June of a year for which the registry holds no newer SCB
   median, **When** eligibility is evaluated, **Then** the answer carries a stale-data warning
   saying a newer median may have been published and naming the median it used.
9. **Given** a user who declares a personal exemption (for example a start-up employer), **When**
   eligibility is evaluated for a non-exempt code, **Then** the 75 % level applies and the answer
   names the declared exemption as the reason, with its conditions and source.

---

### User Story 2 - Find the plausible occupation codes for a job description (Priority: P1)

A user types a job title or a few sentences of duties, in English or Swedish, and gets the closest
SSYK codes ranked, each with its Swedish and English title, how strongly each search method matched
it, the passage of official text that matched, and its legal flags. As they type they get a fast
answer; when they pause or ask for it they get a slower, more thorough answer.

**Why this priority**: Users rarely know their code. Without search the eligibility check needs a
code they do not have.

**Independent Test**: Run the fast and the full search for "backend developer", "sjuksköterska",
"management consultant" and three multi-sentence duty descriptions, and check by hand that the
expected code is in the top five and that timings meet the success criteria.

**Acceptance Scenarios**:

1. **Given** the index is built, **When** a user searches "backend developer" in fast mode, **Then**
   2512 is in the top five and the answer arrives within the fast-mode budget.
2. **Given** the same query in full mode, **When** the search runs, **Then** the results also carry
   the third method's score, the fused ranking uses all three methods, and the answer arrives within
   the full-mode budget.
3. **Given** any search, **When** results are returned, **Then** the answer states that the code
   written on the offer must match the real duties, and no result is ordered or labelled by how low
   its salary threshold is.
4. **Given** a query in English and its Swedish translation, **When** both are searched in full
   mode, **Then** they share most of their top five codes (see SC-004).

---

### User Story 3 - Swedish search is as good as English search (Priority: P1)

Before any change to search ships, the maintainer can see why Swedish queries currently score about
10 points lower than English ones, fix the cause, and show that the cross-lingual benchmark gates
from Feature 001 pass.

**Why this priority**: The constitution blocks merging any search change while the benchmark gates
fail. Story 2 changes search, so this story gates the whole feature.

**Independent Test**: Run the diagnosis, read its report, then run the benchmark and confirm every
gate passes.

**Acceptance Scenarios**:

1. **Given** the Feature 001 benchmark results, **When** the diagnosis runs, **Then** it reports
   recall separately for slash-joined Swedish titles, single Swedish titles and English titles, and
   for the same occupations in both languages, so the share of the gap that comes from query wording
   rather than from the search methods is visible.
2. **Given** the diagnosis shows that part of the gap comes from how the queries were built, **When**
   the query set is corrected, **Then** the correction is recorded with its reason, the benchmark is
   re-run, and the old and new numbers are both kept so the change cannot hide a regression.
3. **Given** the corrections and any search changes, **When** the benchmark runs in full mode, **Then**
   the English–Swedish gap is within 5 points, fused recall in the top five is at least 80 % in each
   language, the fused ranking is at least as good as each single method, and hand-written pairs
   share at least three of their top five codes in at least 80 % of cases.

---

### User Story 4 - Paste a whole job ad and search on the parts that matter (Priority: P2)

A user pastes a full job ad. The system splits it into sentences or short passages and labels each
as the job title, a duty, a skill, company description, benefits or other. The title, duties and
skills are kept for search;
the rest is set aside but shown, so the user can see what was used and why.

**Why this priority**: Real users paste ads, and company blurbs and benefits pull search towards
the wrong codes. Search works without this, so it comes after Stories 1–3.

**Independent Test**: Parse ten labelled real ads (five English, five Swedish), compare the labels
with the hand labels, and compare search on the kept text with search on the raw ad.

**Acceptance Scenarios**:

1. **Given** a pasted English ad with a company paragraph, a duties list, a requirements list and a
   benefits list, **When** it is parsed, **Then** each passage is labelled, the title, duties and
   skills are marked as kept, and the company and benefits passages are marked as not kept.
2. **Given** a pasted ad, **When** the user asks to search it with parsing, **Then** search runs on
   the kept passages only and the answer shows which text was used.
3. **Given** an ad in which no passage is labelled a title, duty or skill, **When** it is parsed and
   searched, **Then** search falls back to the whole ad and says it did so.

---

### User Story 5 - See the salary distribution for an occupation (Priority: P2)

For any code, a user can see the official SCB salary distribution (10th, 25th, 50th, 75th and 90th
percentiles and mean) for the latest year and earlier years, mean salary by age band, the applicable
threshold lines, and, if they ask, a simulated estimate of the distribution for their age band,
clearly marked as simulated, with the formula.

**Why this priority**: The distribution shows where an offer sits in the market, which is what a
user negotiates with. It needs no search, but eligibility (Story 1) is the sharper answer.

**Independent Test**: Read the payload for 2512 and for a code with suppressed cells and compare
every official figure with the SCB statistical database.

**Acceptance Scenarios**:

1. **Given** code 2512, **When** its salary payload is read, **Then** the 2025 figures are median
   53 500, 10th percentile 39 600 and 90th percentile 72 600, the payload names table TAB5932 and
   reference year 2025, and the threshold lines are in the same payload.
2. **Given** a code whose SCB cells are suppressed, **When** its payload is read, **Then** those
   figures are empty and marked as suppressed, and no simulated figure is computed from them.
3. **Given** a request for the 25–34 age band, **When** the payload is read, **Then** the age-adjusted
   percentiles are marked simulated, carry the formula (percentile × age-band mean ÷ all-ages mean)
   and the tables both inputs came from.

---

### User Story 6 - Compare candidate codes side by side (Priority: P2)

A user who has two to five plausible codes sees them side by side: titles, official task
descriptions in Swedish and English, salary distribution summary, legal flags and the threshold
each would need, plus a reminder that the code must match the real duties.

**Why this priority**: Honest fit means showing the consequences of every plausible code next to
its official task text. It combines Stories 1, 2 and 5.

**Independent Test**: Compare 2512, 2511 and 3512 and check each column against the profile,
salary and eligibility answers for the same code.

**Acceptance Scenarios**:

1. **Given** codes 2512, 2511 and 3512, **When** they are compared, **Then** each appears with its
   official task text in both languages, its salary summary, its legal flags and its threshold,
   in the order the user gave them.
2. **Given** an offer context (salary, date, application type), **When** codes are compared,
   **Then** each column shows pass or fail for that offer under that code.
3. **Given** one code or six codes, **When** a comparison is requested, **Then** it is refused with
   a message that states the allowed range.

---

### User Story 7 - Read the legal timeline and the rules in force (Priority: P3)

A user or a later surface can read every salary rule the registry holds — each threshold percentage,
each SCB median, each exemption and ban — with the period it applies to, its source and the date it
was last checked.

**Why this priority**: It explains the eligibility answers and feeds the legal guide in Feature 004,
but nothing in this feature depends on it.

**Independent Test**: Read the timeline and check every row against Migrationsverket and SFS 2026:605.

**Acceptance Scenarios**:

1. **Given** the registry, **When** the timeline is read, **Then** it lists the medians from June
   2021 to June 2026 and the rule changes (flat 13 000 SEK, 80 % from 1 November 2023, 90 % from 1
   June 2026, the transition ending 1 December 2026), each with dates and a source link.

---

### Edge Cases

- Application date before 1 November 2023: the answer says the date is outside the period the
  registry covers rather than applying a rule it does not hold.
- Application date in the future: evaluated under the rules known today, with the stale-data
  warning if a new median is due before that date.
- Extension filed in the transition window for a permit granted on or after 1 June 2026: the
  transitional 80 % rule does not apply.
- An exempt code (75 %) on an extension filed in the transition window: judged at 80 % with a
  warning that 75 % may apply (FR-012).
- A declared personal exemption on a banned code: banned wins.
- Salary exactly at the threshold: passes (the requirement is "at least").
- Share of full time of zero, above 100 % or not a number; negative salary; unknown or malformed
  code: refused with a message naming the field.
- Slash-joined search text such as "Aktuarie/Försäkringsaktuarie": each title is searched and the
  results merged (FR-013a); a slash inside ordinary prose is not a title list.
- Empty search text, or text beyond the length limit: refused with a message stating the limit.
- Search text that matches nothing well (for example "asdf"): results are still ranked but the
  answer carries a low-confidence note.
- Full mode requested when the slower model is unavailable: the answer falls back to fast mode and
  says so; it does not fail.
- A code that SCB does not publish salaries for (one of the reconciliation gaps from Feature 001):
  eligibility still works from the national median; the salary payload says there is no
  occupation-level data.
- Duplicate codes in a comparison: duplicates are dropped before the 2–5 count is checked.

## Requirements *(mandatory)*

### Functional Requirements

**Legal registry**

- **FR-001**: Every legal threshold, percentage, median, date, exempt code, ban and exemption
  category MUST live in one registry. Each row MUST have an effective-from date, an optional
  effective-to date, a source link and a checked-on date. The existing occupation flags from
  Feature 001 MUST be read from this registry rather than kept separately.
- **FR-002**: The registry MUST hold the SCB medians from June 2021 to June 2026 with the date each
  took effect, and the rule history: 13 000 SEK flat, 80 % from 1 November 2023, 90 % from 1 June
  2026, 75 % for exempt codes and personal exemptions from 1 June 2026, and the transitional 80 %
  rule for extensions filed 1 June–1 December 2026 on permits granted before 1 June 2026.
- **FR-003**: The median that governs an application MUST be the latest one published on the day
  the application is filed.
- **FR-004**: Threshold amounts MUST be derived from the registry's percentage and median and MUST
  equal the amounts Migrationsverket publishes (34 470, 28 725 and 33 390 SEK in the scenarios
  above).
- **FR-005**: The system MUST warn when the evaluation date is after 16 June of a year and the
  registry holds no median published that year. The warning MUST name the median used.

**Eligibility**

- **FR-006**: The eligibility operation MUST take: code, monthly salary in SEK before tax, share of
  full time, application type (first permit or extension), filing date, prior-permit grant date
  (extensions only), and zero or more declared personal exemptions.
- **FR-007**: It MUST return: whether a permit is possible for the code, the rule applied, the
  percentage, the median and its SCB reference year, the threshold in SEK, pass or fail, margin in
  SEK and percent, the reason for the rule chosen, warnings, and every source with its checked-on
  date.
- **FR-008**: Salary at exactly the threshold MUST pass.
- **FR-009**: For banned codes the answer MUST be "not permitted", independent of salary. For the
  partial ban on 9210 the answer MUST carry a warning naming the banned job.
- **FR-010**: When the share of full time is below 100 %, the answer MUST say that the threshold
  applies to the monthly salary actually paid and is not reduced for part-time.
- **FR-011**: Every answer MUST state that the salary must also be in line with the relevant
  collective agreement or industry practice, which this tool does not check, and that the result is
  information, not legal advice.
- **FR-012**: For an exempt code on an extension filed in the transition window, pass or fail
  MUST use the transitional 80 % rule, and the answer MUST warn that the 75 % level may apply
  instead, cite the transitional provision and the exemption, and advise confirming with
  Migrationsverket.

**Search**

- **FR-013**: Search MUST accept free text in English or Swedish (other languages best effort) and
  return the top k codes (default 5, at most 20), each with code, Swedish and English titles,
  fused rank, per-method score and rank, the matched official text, and the code's legal flags.
- **FR-013a**: When the search text is a list of titles joined by "/", search MUST treat each part
  as an alternative, search each part and merge the results into one ranking.
- **FR-014**: Search MUST offer a fast mode (meaning model plus keyword search) and a full mode
  (adds the second meaning model). If the second model cannot be loaded, full mode MUST fall back
  to fast mode and say so.
- **FR-015**: Search results MUST NOT be ordered, filtered or labelled by salary threshold, and
  every answer MUST carry the honest-fit statement.
- **FR-016**: Search MUST return a low-confidence note when no result scores well enough to be
  useful. The cut-off MUST be set from the benchmark, not guessed.
- **FR-017**: The search and the benchmark MUST use the same ranking code, so benchmark numbers
  describe what users get.

**Search quality**

- **FR-018**: A diagnosis MUST break benchmark recall down by language, query origin (hand-written
  or generated) and query form (single title or slash-joined), and report how much of the English–
  Swedish gap each accounts for. Its output MUST be saved beside the benchmark results.
- **FR-019**: Slash-joined benchmark queries MUST stay as they are; the slash handling in FR-013a
  is the fix for them. Any other correction to the benchmark queries MUST be justified by the
  diagnosis, recorded with its reason, and keep generated query titles out of the indexed text. The results from
  before the correction MUST be kept for comparison.
- **FR-020**: Before this feature is merged, full mode MUST pass every benchmark gate (top-five
  recall ≥ 80 % per language, English–Swedish gap ≤ 5 points, fused at least as good as each single
  method, hand-written pair overlap ≥ 80 %), and fast mode MUST reach top-five recall ≥ 80 % in
  each language. The benchmark MUST report both modes.

**Job-ad parsing**

- **FR-021**: The system MUST split a pasted ad into passages and label each as title, duty,
  skill, company, benefits or other, with a keep flag that is true for titles, duties and skills
  only.
- **FR-022**: Parsing MUST work for English and Swedish ads and MUST NOT need an LLM or network
  access.
- **FR-023**: Search MUST optionally parse its input first, run on the kept passages, return which
  text was used, and fall back to the whole input when nothing is kept.

**Salary payloads**

- **FR-024**: The salary payload for a code MUST include each available year's percentiles and
  mean, mean salary and headcount by age band, the threshold lines in force on the request date
  (90 %, 75 % and the one that applies to the code), and for every figure the SCB table, reference
  year and fetch time.
- **FR-025**: Suppressed figures MUST stay empty and be listed as suppressed. No figure may be
  filled in, interpolated or carried over from another year.
- **FR-026**: On request for an age band, the payload MUST add age-adjusted percentiles computed as
  percentile × age-band mean ÷ all-ages mean, each marked simulated with the formula and the input
  tables. If any input is empty, the simulated figure MUST be empty.

**Comparison**

- **FR-027**: Comparison MUST accept 2–5 distinct codes and return, per code in the given order,
  titles, official task descriptions in both languages, the latest salary summary, legal flags,
  the applicable threshold and, when an offer context is given, the eligibility answer.
- **FR-028**: Comparison MUST carry the honest-fit statement and MUST NOT rank or recommend codes
  by threshold.

**Interface**

- **FR-029**: Every operation above, plus occupation lookup by code, the legal timeline and the
  latest benchmark results, MUST be available through a versioned web API (version 1) with a
  published, machine-readable description of every request and response.
- **FR-030**: Request and response shapes MUST be defined once and reused by later surfaces (MCP,
  A2A, web client).
- **FR-031**: Invalid input MUST be refused with a message that names the field and the rule it
  broke. No operation may expose internal errors or file paths.
- **FR-032**: No operation in this feature may require the OpenRouter key.
- **FR-033**: Request contents (ad text, salaries, dates, declared exemptions) MAY be written to
  local debug logs, MUST NOT be stored anywhere else, and MUST be deleted after 7 days. Logs MUST
  NOT be committed, and evidence transcripts MUST use made-up or public ads and offers only.

### Key Entities

- **Legal rule**: a threshold percentage, flat amount, exemption, ban or transitional provision,
  with the codes or applicant categories it covers, effective period, source link and checked-on
  date.
- **Median record**: an SCB national median, its reference year, the date it took effect for
  permits, source link and checked-on date.
- **Eligibility request**: code, salary, share of full time, application type, filing date,
  prior-permit date, declared exemptions.
- **Eligibility answer**: permitted or not, rule applied and why, percentage, median, threshold,
  pass/fail, margin, warnings, sources, disclaimer.
- **Search hit**: code, titles, fused rank, per-method scores and ranks, matched text, legal flags.
- **Search answer**: mode used (and fallback, if any), text searched, hits, low-confidence flag,
  honest-fit statement.
- **Ad passage**: text, position, label, keep flag.
- **Salary payload**: code, yearly distributions, age-band means, threshold lines, optional
  simulated age-adjusted percentiles, sources.
- **Comparison**: the ordered list of codes with their profile, salary and eligibility columns.
- **Gap diagnosis**: recall by language, origin and query form, and the share of the gap each
  explains.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every eligibility boundary case in User Story 1 and the edge cases gives the answer
  Migrationsverket and SFS 2026:605 give, checked by hand against the sources.
- **SC-002**: No threshold amount, percentage, median or date appears anywhere outside the registry
  except in tests of the registry.
- **SC-003**: Fast search returns within 50 ms for 95 % of single-title queries, and full search
  within 1 second for 95 % of queries up to the length of a typical ad, measured on the
  maintainer's laptop with models loaded.
- **SC-004**: In full mode the benchmark gates pass: top-five recall ≥ 80 % in each language, English–Swedish
  gap ≤ 5 points, fused at least as good as each single method, and hand-written English–Swedish
  pairs sharing at least three of their top five codes in ≥ 80 % of pairs. In fast mode, top-five
  recall is ≥ 80 % in each language.
- **SC-005**: On ten hand-labelled real ads (five per language), at least 85 % of passages get the
  hand label, and search on the kept passages puts the correct code in the top five at least as
  often as search on the raw ad.
- **SC-006**: Every salary figure in every payload matches the stored SCB figure exactly, every
  payload names its table and reference year, and every simulated figure is marked simulated.
- **SC-007**: No search, comparison or eligibility answer recommends a code or orders codes by how
  low their threshold is, checked by a test over all answers.
- **SC-008**: A scripted run against the running service exercises every operation once and saves
  its requests and responses as evidence.

## Assumptions

- The salary a user enters is the gross monthly salary actually paid, so it is compared with the
  threshold as it is. Benefits, allowances and overtime are not added.
- Personal exemptions (start-up employer under 5 years old with under 100 staff, former student,
  licensed profession, temporary protection) are declared by the user; the system lists their
  conditions but does not verify them.
- Eligibility is supported for applications filed from 1 November 2023. The 13 000 SEK flat rule
  appears in the timeline only.
- Applications are judged on the filing date. Whether Migrationsverket can apply a newer median
  published while an application is pending is out of scope.
- "Typical ad" means up to about 600 words. The search length limit is set to comfortably cover
  long ads.
- The ten real ads for the parsing test are taken from public JobTech job ads and labelled by the
  maintainer.
- The Swedish hand-written benchmark queries still await a native speaker's review; the gates are
  measured on them as they stand, and the review may change them later.
- Out of scope: MCP and A2A (Feature 003), the web client and Docker (Feature 004), live job-ad
  counts (Feature 005), checking collective agreements, the 001 cold-rebuild time, the data
  dictionary source errors, and Milvus server-mode vocabulary.
