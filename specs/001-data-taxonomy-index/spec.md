# Feature Specification: SSYK Occupation Dataset and Bilingual Search Index

**Feature Branch**: `001-data-taxonomy-index`

**Created**: 2026-10-20

**Status**: Draft

**Input**: User description: "Feature 001 data-taxonomy-index: build the canonical SSYK 2012 occupation
dataset and a bilingual search index for Lönekrav — canonical profiles reconciling the SCB, ISCO and
JobTech code lists, official SCB salary statistics with age bands, a two-model plus keyword search index,
a cross-lingual benchmark, a data dictionary, and a repeatable pipeline that runs without an LLM key."

## Clarifications

### Session 2026-10-20

- Q: Where should benchmark gold labels come from? → A: Hybrid: about 30 hand-written EN/SV pairs
  (duties, look-alikes) plus 200+ title queries generated from official JobTech title-to-code
  mappings; generated query titles are held out of the indexed text.
- Q: Which salary years should the dataset hold? → A: 2014 to the latest published year, from both
  SCB SSYK 2012 tables.
- Q: How does a fresh machine or image get the index? → A: Commit the small processed data; rebuild
  the index from it locally or during the image build. Nothing large in git.
- Q: Does the benchmark run in the normal test suite? → A: No. The default suite stays fast and
  offline with a tiny fixture index; a separately marked benchmark run gates changes to data and
  search.

## User Scenarios & Testing *(mandatory)*

The direct users of this feature are the maintainer and the later Lönekrav features (search,
eligibility, protocols, web client). The people it ultimately serves are non-EU job seekers who search
mostly in English, sometimes in Swedish, and need correct occupation and salary facts.

### User Story 1 - Look up a complete, trustworthy occupation profile (Priority: P1)

Given a 4-digit SSYK 2012 code, the maintainer (and every later feature) can read one profile that
holds the official Swedish and English titles, official task descriptions in both languages, job-title
synonyms in both languages, links to the international classifications, and the legal flags that
decide which salary requirement applies.

**Why this priority**: Every other feature reads these profiles. Without them nothing can be searched,
compared or explained.

**Independent Test**: Run the build step, open the profile for 2512 (software and system developers),
3511 (ICT operations technicians, exempt) and 5343 (personal assistants, banned), and check every
field against the official sources by hand.

**Acceptance Scenarios**:

1. **Given** the pipeline has been built, **When** the profile for 2512 is read, **Then** it shows the
   Swedish title "Mjukvaru- och systemutvecklare m.fl.", the SCB English title "Software- and system
   developers", at least 20 Swedish synonyms, English synonyms, ISCO-08 links to 2511, 2512, 2513,
   2514 and 2521, and no legal flags.
2. **Given** the pipeline has been built, **When** the profile for 3511 is read, **Then** it is
   flagged as exempt from the 90 % requirement with the 75 % level, citing SFS 2026:605.
3. **Given** the pipeline has been built, **When** the profile for 5343 is read, **Then** it is
   flagged as banned from work permits, and 9210 carries a partial-ban flag for forest berry pickers
   only, both citing SFS 2026:605.
4. **Given** a code that one source lacks (for example a manager "nivå 2" code missing from JobTech),
   **When** its profile is read, **Then** it is still complete from the other sources and the gap is
   listed in the discrepancy report.

---

### User Story 2 - See official salary statistics for an occupation (Priority: P1)

For any code, the maintainer can read the official SCB monthly salary distribution (10th, 25th, 50th,
75th and 90th percentiles and mean, with published confidence intervals) for each available year from
2014 to 2025, plus mean salary and headcount by age band, each figure labelled with its source table,
reference year and fetch time.

**Why this priority**: The salary comparison is the purpose of the product. It is equal first with the
profiles because neither is useful alone.

**Independent Test**: Build the dataset and compare five codes, including one with suppressed cells,
against the SCB statistical database web interface.

**Acceptance Scenarios**:

1. **Given** the dataset is built, **When** salary statistics for "all occupations" in 2025 are read,
   **Then** the median is 38 300 SEK, matching the figure Migrationsverket uses for the current
   threshold.
2. **Given** the dataset is built, **When** 2025 statistics for 2512 are read, **Then** they match SCB
   exactly (median 53 500, 10th percentile 39 600, 90th percentile 72 600) and name table TAB5932.
3. **Given** SCB suppressed a value (for example the 18–24 headcount for 2512 in 2025), **When** it
   is read, **Then** it is empty and flagged as suppressed, never estimated.

---

### User Story 3 - Find the right occupation in any language (Priority: P2)

Given a query in English or Swedish — a job title, a sentence of duties, or several paragraphs — the
maintainer can get a ranked list of the most similar occupations from each of three methods (a
Swedish-centred meaning model, a multilingual meaning model, keyword matching) and from their fused
ranking.

**Why this priority**: Search is the core interaction of the product, but it depends on stories 1 and
2 and is exercised by users only through later features.

**Independent Test**: Build the index, then query "backend developer", "sjuksköterska" and
"management consultant" and check that the expected code is in the top five for each method.

**Acceptance Scenarios**:

1. **Given** the index is built, **When** "backend developer" is queried, **Then** 2512 is in the
   fused top five.
2. **Given** the index is built, **When** the same query is made in English and in Swedish, **Then**
   the fused top-five lists share at least three codes.
3. **Given** the index file has been copied to another machine, **When** it is queried there, **Then**
   it returns the same results without rebuilding.

---

### User Story 4 - Prove that query language does not change results (Priority: P2)

The maintainer can run a benchmark of hand-written English/Swedish query pairs plus generated
title queries, and get, per
method and for the fused ranking, the share of queries whose correct occupation ranks first, ranks in
the top five, and the mean reciprocal rank, split by language. The results are saved in a file that the
web client can later display.

**Why this priority**: The product claims that language does not matter. This story makes the claim
checkable and protects it from regressions.

**Independent Test**: Run the benchmark and read the saved results file.

**Acceptance Scenarios**:

1. **Given** the index is built, **When** the benchmark runs, **Then** it reports Recall@1, Recall@5
   and MRR for each method and language and writes them to a results file with the run date and
   model versions.
2. **Given** the benchmark set, **When** it is inspected, **Then** it has at least 30 hand-written
   pairs and at least 200 generated title queries, and it contains short titles,
   single-sentence duties, multi-sentence descriptions and look-alike pairs (for example data analyst
   versus statistician versus organisation developer; nurse specialities; manager level 1 versus
   level 2).
3. **Given** a generated title query, **When** the index is inspected, **Then** that exact title is
   not part of the indexed text.
4. **Given** a normal test run, **When** the suite runs, **Then** no model download is needed and the
   benchmark is skipped; **When** the benchmark run is requested, **Then** it fails if fused Recall@5
   falls below SC-004 or the language gap exceeds SC-005.

---

### User Story 5 - Rebuild everything with one repeatable command sequence (Priority: P3)

The maintainer can fetch, build, index and benchmark from scratch, or re-run any step, and get the same
result. No LLM key is needed. Measured speed and memory of both meaning models are recorded.

**Why this priority**: Needed every June when SCB publishes new figures, but the first build can be
done step by step.

**Independent Test**: Delete all generated files, run the four steps, and compare the outputs with the
previous run.

**Acceptance Scenarios**:

1. **Given** no LLM key is configured, **When** all four steps run, **Then** they complete and every
   required profile field is filled.
2. **Given** a completed build, **When** the build step is re-run with cached downloads, **Then** the
   outputs are byte-identical apart from timestamps.
3. **Given** a fresh clone with the committed processed data, **When** the index step runs, **Then**
   it rebuilds the index without fetching from SCB, JobTech, ILO or ESCO.
4. **Given** a source is unreachable, **When** fetch runs, **Then** it fails with a message naming the
   source and URL, and leaves earlier cached data intact.

### Edge Cases

- A code exists in the salary table but not in the SCB structure file, or the reverse: it is kept,
  flagged, and listed in the discrepancy report with which sources have it.
- JobTech merges manager levels (for example 1210 for 1211 and 1212): its titles and descriptions are
  attached to both SCB codes and marked as shared.
- One SSYK code maps to several ISCO-08 groups (2512 maps to five): all are linked, and their English
  descriptions are kept separately with their ISCO code, not blended.
- SCB uses the special codes 0000 (all occupations), 0001 (other) and 0002 (unknown): 0000 is stored
  as the national reference row; 0001 and 0002 are excluded from profiles and search.
- An age band or percentile is suppressed for a small occupation: the value is empty and flagged, and
  the profile is still built.
- An ESCO or ILO description is missing for a code: the profile falls back to the SCB/JobTech text
  and records the absence.
- A new SCB year appears: fetch picks it up without code changes, and older years are kept.
- The 2014–2022 and 2023-onward SCB tables overlap or differ in layout: each year is taken from
  exactly one table, recorded per figure.
- An LLM-generated synonym duplicates an official one: the official one is kept and the duplicate
  dropped.

## Requirements *(mandatory)*

### Functional Requirements

**Occupation profiles**

- **FR-001**: The system MUST produce exactly one profile for each 4-digit SSYK 2012 occupation found
  in any official SCB source, excluding the special codes 0001 and 0002.
- **FR-002**: The system MUST produce a discrepancy report listing, for each code, which sources
  (SCB structure, SCB salary table, SCB ISCO key, SCB title index, JobTech) contain it.
- **FR-003**: Each profile MUST contain the official Swedish title and the official SCB English
  title.
- **FR-004**: Each profile MUST contain the official Swedish description and, where published, the
  English descriptions and task lists of each linked ISCO-08 group, each labelled with its source.
- **FR-005**: Each profile MUST contain Swedish job-title synonyms from the SCB title index and
  JobTech, and English and Swedish occupation labels from ESCO, each labelled with its source and
  language, with exact duplicates removed.
- **FR-006**: Each profile MUST list its linked ISCO-08 codes and the ESCO occupations reached through
  them.
- **FR-007**: Each profile MUST carry legal flags: exempt from the 90 % requirement (75 % level
  applies) for the 27 codes listed in SFS 2026:605, banned for 5343, and partially banned for 9210
  (forest berry pickers only), each flag citing the ordinance and its effective date.
- **FR-008**: The system MAY add LLM-generated English job titles. Each MUST be labelled as LLM
  output with the model name and date, and the dataset MUST be complete and valid without them.

**Salary statistics**

- **FR-009**: The system MUST store, for each code and each available year from 2014 onwards, the
  official SCB 10th, 25th, 50th, 75th and 90th percentiles and mean monthly salary for all sectors and
  both sexes combined, with the published 95 % confidence intervals.
- **FR-010**: The system MUST store, for each code and each available year from 2014 onwards, mean monthly salary and headcount for the
  age bands 18–24, 25–34, 35–44, 45–54, 55–64 and 65–68, and for all ages.
- **FR-011**: The system MUST store the "all occupations" row as the national reference.
- **FR-012**: Every stored figure MUST carry its source table, reference year and fetch time.
- **FR-013**: Suppressed or missing values MUST be stored as empty and flagged. No value may be
  estimated, interpolated or carried over from another year or group.

**Search index**

- **FR-014**: The system MUST build a single portable index file, rebuildable from the committed
  processed data alone, that ranks occupations against a
  query by each of three methods: a Swedish-centred meaning model, a multilingual meaning model, and
  keyword matching over Swedish and English text.
- **FR-015**: The index MUST also return a fused ranking that combines the three methods.
- **FR-016**: Each result MUST include the code, both titles, the score from each method, and the
  fused rank.
- **FR-017**: The system MUST record, for each meaning model, the measured time to process a short
  query and a long pasted description on an ordinary laptop processor, and the memory it needs.

**Benchmark**

- **FR-018**: The system MUST include a benchmark with (a) at least 30 hand-written queries, each in
  English and in Swedish, covering short titles, single-sentence duties, multi-sentence descriptions
  and look-alike pairs, each labelled with one or more acceptable codes; and (b) at least 200 title
  queries generated from official JobTech title-to-code mappings, in Swedish and, where ESCO gives
  one, English.
- **FR-018a**: Titles used as generated benchmark queries MUST be excluded from the indexed text, so
  the benchmark measures matching rather than lookup.
- **FR-019**: The benchmark MUST report Recall@1, Recall@5 and MRR for each method and the fused
  ranking, separately for each language, and the difference between languages.
- **FR-020**: The benchmark MUST save its results, the run date and the model identifiers to a file
  that later features can read.
- **FR-020a**: The default test run MUST NOT need model downloads or network access. The benchmark
  MUST run as a separately requested test run that fails when SC-004 or SC-005 is not met.

**Documentation and pipeline**

- **FR-021**: The system MUST provide a data dictionary describing every output table and column,
  its meaning, units, source, licence and required attribution.
- **FR-021a**: The processed profiles and salary tables MUST be committed. Raw downloads, the
  index file and model weights MUST NOT be committed.
- **FR-022**: The system MUST provide four separately runnable steps — fetch, build, index,
  benchmark — that can be re-run safely and give the same output for the same inputs.
- **FR-023**: Fetch MUST cache raw downloads locally and MUST NOT overwrite a good cache with a
  failed download. Failure messages MUST name the source and the address that failed.
- **FR-024**: No step except the optional LLM enrichment may require an LLM key.

### Key Entities

- **Occupation profile**: one SSYK 2012 4-digit occupation. Code, Swedish and English titles,
  descriptions by language and source, synonyms by language and source, ISCO-08 and ESCO links, legal
  flags, source coverage.
- **Salary distribution**: one occupation, one year (2014 onwards). Percentiles, mean, confidence intervals,
  suppression flags, source table, reference year, fetch time.
- **Age-band salary**: one occupation, one year, one age band. Mean salary, headcount, suppression
  flags, source.
- **Legal flag**: an occupation's status under SFS 2026:605: exempt (75 % level), banned or
  partially banned. Includes citation and effective date.
- **Discrepancy record**: one code and the list of sources that contain it.
- **Benchmark query**: a hand-written English/Swedish pair or a generated title, its query type,
  origin (hand-written or generated), and the acceptable correct codes.
- **Benchmark result**: one method, one language, the three metrics, the run date and the model
  identifiers.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100 % of occupations in the SCB salary table have a profile with both official titles
  and at least one description.
- **SC-002**: Salary figures for 10 hand-picked occupations match the SCB statistical database
  exactly, and the 2025 national median equals 38 300 SEK.
- **SC-003**: No stored salary figure lacks a source table and reference year, and no suppressed
  figure has a value.
- **SC-004**: In the benchmark, the fused ranking puts the correct occupation in the top five for at
  least 80 % of queries in each language.
- **SC-005**: For the fused ranking, Recall@5 differs between English and Swedish queries by no more
  than 5 percentage points.
- **SC-006**: The fused ranking scores at least as well on Recall@5 as each single method, in both
  languages.
- **SC-007**: A full rebuild from an empty cache completes in under 60 minutes on the maintainer's
  laptop, and a rebuild from cache in under 15 minutes.
- **SC-008**: The portable index file is under 200 MB.

## Assumptions

- The latest published SCB year (currently 2025) is the default year for later features. Years
  from 2014 are kept for trend views. SSYK 2012 figures before 2014 do not exist.
- "All sectors, both sexes" is the only cut stored, as decided in planning, to minimise suppressed
  cells.
- The 27 exempt codes and the bans are taken from SFS 2026:605, published 23 May 2026. Later changes
  to the list are handled by updating the legal registry, which is outside this feature.
- ESCO and ILO data may be reused with attribution. The exact licence wording is confirmed during
  implementation and recorded in the data dictionary.
- The two meaning models are KBLab's Swedish sentence-BERT and Microsoft Harrier 0.6B, as decided in
  planning. If Harrier cannot meet the memory budget, a smaller multilingual model can replace it
  through the same slot. That decision is recorded with the measurements.
- The hand-written benchmark queries are written by the maintainer and the agent, in both
  languages, and reviewed by a Swedish speaker before the results are published.
- Out of scope: API endpoints, job-ad parsing, eligibility logic, user interface, job-ad market data.
