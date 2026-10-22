# Feature Specification: Lönekrav web client and container

**Feature Branch**: `004-web-client-docker`

**Created**: 2026-10-22

**Status**: Draft

**Input**: User description: "004-web-client-docker. English single-page app with: legal guide +
timeline + part-time calculator; paste/typing search with signal-vs-fluff highlighting and a
per-model score strip (kblab/BM25 instant, Harrier arrives on pause); distribution chart per
selected code (P10–P90 bar, floor line at the applicable threshold, P10–P25 band, age-band mean
dots, toggleable simulated age-adjusted ghost bar, up to 4 codes); compare view with official task
text; A2A chat drawer that can select codes on the chart. `docker compose up --build` serves
everything on one port. Plan notes: Vite + React 19 + TS + Tailwind; chart as hand-written SVG
following the dataviz skill and viz-distributions; frontend/src/lib/a2aClient.ts (JSON-RPC over
fetch + SSE parsing); typed client generated from the FastAPI OpenAPI schema. Multi-stage
Dockerfile: node build → python 3.12-slim with uv sync --frozen, models pre-downloaded into the
image (or a cache volume), FastAPI serves frontend/dist; compose sets mem_limit to the measured
budget (4 GB). Document the Cloud Run variant in the README without deploying it. The A2A agent
card URL (hard-coded to localhost:8000 in 003) must become configurable. Verify: Playwright
screenshots of the three main views at phone and desktop width; docker stats RSS recorded;
end-to-end: paste a real LinkedIn ad in English, then its Swedish translation, confirm the same
top-3 codes; A2A drawer updates the chart."

## User Scenarios & Testing *(mandatory)*

Features 001–003 built the data, the search, the eligibility rules and three machine interfaces
(REST, MCP, A2A). Nobody without a terminal can use them yet. Feature 004 gives job seekers,
employers and advisers a web page, and packages the whole stack so that one command runs it on any
machine.

The people using the page are:

- **A job seeker** with a non-EU passport who has an offer, or is negotiating one, and needs to
  know which SSYK code the job sits under and what salary that code requires.
- **An employer or recruiter** writing the offer, who must put a code on it that matches the real
  duties.
- **An adviser** (union, university careers office, relocation firm) explaining the rules to
  either of them.

The page is in English. Swedish SSYK titles and legal terms appear next to the English ones so
that users can copy them into Swedish forms.

### User Story 1 - Find the codes that fit a job (Priority: P1)

A user types a job title, or pastes a whole job ad in English, Swedish or another language. While
they type, a ranked list of SSYK codes updates. When they pause, a slower and more accurate search
refines the list. For a pasted ad, the page shows which parts of the ad describe the job (duties,
requirements) and which were set aside as fluff (company pitch, benefits, how to apply), so the
user can see what the search actually read. Each result shows its Swedish and English titles, the
passage that matched, any legal flags (an exempt code with a lower threshold, a banned code), and a
small strip showing how each search method ranked it. The honest-fit notice is visible next to the
results.

**Why this priority**: Finding the code is the first question every user has, and every other view
starts from a selected code.

**Independent Test**: Open the page, type a title letter by letter and watch the list update; paste
a long ad and check the highlighting and the refined list; compare the codes with the REST search
response for the same text.

**Acceptance Scenarios**:

1. **Given** the search box, **When** the user types "backend developer" one character at a time,
   **Then** the result list updates during typing, without waiting for the user to stop, and never
   shows results for older text after results for newer text.
2. **Given** a typed query, **When** the user stops typing, **Then** within a few seconds the list
   is replaced by the accurate search's ranking, and the page shows which search produced the list
   on screen.
3. **Given** a pasted job ad, **When** the results arrive, **Then** each passage of the ad is shown
   as kept or set aside, with the reason in words (for example "under a 'Benefits' heading"), and
   the user can see the text the search used.
4. **Given** any result, **When** it is displayed, **Then** it shows the code, the Swedish and
   English titles, the passage that matched, its legal flags with their sources, and one rank per
   search method. A method that did not run (for example the accurate model before the pause, or
   when it is unavailable) is shown as not run, not as a rank of zero.
5. **Given** the accurate model cannot be loaded, **When** the user pauses, **Then** the page keeps
   the fast results and says why the accurate search did not run.
6. **Given** a result, **When** the user selects it, **Then** that code is added to the salary
   chart (Story 2) and the comparison (Story 3).

---

### User Story 2 - See what each code pays and what it requires (Priority: P1)

For up to four selected codes, the user sees one chart. Each code has a horizontal bar from the
10th to the 90th percentile of SCB's monthly salary, with the median marked, the 10th–25th
percentile range shaded as the low-pay band, and the mean salary of each age band shown as dots. A
vertical line marks the salary floor that applies to that code (the general level, or the lower
level for exempt codes) and is labelled with its rule and amount. The user can switch on a ghost
bar per code: an age-adjusted estimate for a chosen age band, clearly labelled as simulated, with
the formula available. The SCB table and reference year are shown under the chart. A suppressed
SCB value shows as a gap with a note, never as an estimate.

**Why this priority**: The salary picture against the floor is what users came for. It turns a
code into a negotiating position.

**Independent Test**: Select two codes, one with an exempt threshold, and check every mark on the
chart against the REST salary payload for each code; switch the simulated bar on and off; pick a
code with a suppressed percentile.

**Acceptance Scenarios**:

1. **Given** one to four selected codes, **When** the chart is drawn, **Then** every percentile,
   age-band mean and threshold on it equals the corresponding value in the REST salary payload for
   that code, and every bar shows its exact value on hover, focus or tap.
2. **Given** an exempt code and a non-exempt code, **When** both are on the chart, **Then** each
   has its own floor line at its own applicable level, each labelled with its rule.
3. **Given** the simulated bar is switched on for an age band, **When** it is drawn, **Then** it is
   visually distinct from the official bars (for example outlined and lighter), is labelled
   "simulated", and its formula and inputs can be shown. Switching it off removes it.
4. **Given** a code whose SCB value is suppressed, **When** it is drawn, **Then** the missing value
   is left out with a note saying that SCB does not publish it, and nothing is drawn in its place.
5. **Given** four codes already on the chart, **When** the user tries to add a fifth, **Then** the
   page says that the chart holds at most four and asks the user to remove one first.
6. **Given** the chart, **When** a screen reader or keyboard user reaches it, **Then** the same
   figures are available as a table.

---

### User Story 3 - Compare codes side by side (Priority: P2)

The user compares the selected codes (two to five). For each code they see its official Swedish
task description from SCB, its English description, its salary summary, its threshold and legal
flags. If they have entered an offer, they also see whether that offer would pass under each code,
and by what margin. The honest-fit notice states that the code has to match the duties actually
performed.

**Why this priority**: Comparison is where the honest-fit framing matters most, but it needs codes
selected first.

**Independent Test**: Select three codes, enter an offer, and check each column against the REST
compare response.

**Acceptance Scenarios**:

1. **Given** two to five selected codes, **When** the compare view opens, **Then** each code shows
   its official task text with its source, its salary summary, threshold, flags and, with an offer,
   pass or fail with the margin and warnings, all equal to the REST compare response.
2. **Given** an offer that passes under one code and fails under another, **When** the comparison
   is shown, **Then** the page states that the code must match the real duties, and no wording,
   ordering or highlighting suggests choosing the code that passes.
3. **Given** fewer than two codes, **When** the user opens the compare view, **Then** it explains
   that comparison needs at least two codes and links back to search.

---

### User Story 4 - Understand the law and check an offer (Priority: P2)

A user who wants the rules rather than a code reads a short legal guide: what the salary
requirement is, how it is calculated, when the rule changed, which codes are exempt or banned, and
how extensions filed during the transition are treated. A timeline shows every median and rule
change. A calculator takes an offer (monthly salary, share of full time, application type, dates,
any personal exemptions, and a code) and says whether it passes, by how much, and with which
warnings, including the warning that a part-time salary must still reach the full threshold. Every
legal statement links its source and shows when it was checked, and the page states that it is
information, not legal advice.

**Why this priority**: The legal guide is needed for trust and for users who arrive with a code
already, but the search and chart answer the more common question.

**Independent Test**: Open the guide, check every timeline entry against the REST timeline, and run
the calculator for a full-time pass, a part-time fail, an extension in the transition window and a
banned code, comparing each with the REST eligibility answer.

**Acceptance Scenarios**:

1. **Given** the guide, **When** it is displayed, **Then** every figure and date in it comes from
   the legal registry through the API, and each statement shows its source link and checked-on
   date.
2. **Given** the timeline, **When** it is displayed, **Then** it lists the same events as the REST
   timeline, in date order.
3. **Given** an offer at less than full time, **When** the calculator runs, **Then** it shows the
   part-time warning with its source, and the result equals the REST eligibility answer.
4. **Given** an invalid offer (for example a decision date before the filing date), **When** the
   user submits it, **Then** the calculator names the field and the problem, in the user's terms.

---

### User Story 5 - Ask the advisor (Priority: P3)

From any view, the user opens a chat drawer, pastes an ad, writes a line about their background
and, optionally, their offer. While the advisor works, the drawer shows its progress ("reading the
job ad", "searching occupations"). Each time the advisor looks up a code's salary or compares
codes, those codes are selected on the chart, so the user can see what the advisor is looking at.
At the end the drawer shows the advisor's memo, including its honest-fit text, the not-legal-advice
statement and the notice that a third-party model wrote it. Before sending, the drawer tells the
user that their message goes to a third-party model service.

**Why this priority**: The advisor is the showcase, but it needs a paid model key and depends on
every other view.

**Independent Test**: With a key, send an ad and check that the chart selection follows the
advisor's lookups and that the memo appears; without a key, check that the drawer explains that the
advisor is unavailable and that the rest of the page works.

**Acceptance Scenarios**:

1. **Given** the drawer, **When** the user sends a request, **Then** progress messages appear as
   they arrive, not all at once at the end.
2. **Given** the advisor looks up salary or compares codes, **When** that result arrives, **Then**
   those codes are selected on the chart (within the four-code limit) and the chart shows the
   result's data.
3. **Given** the run completes, **When** the memo arrives, **Then** it is shown as formatted text
   with its footer intact.
4. **Given** the server has no model key, **When** the user opens the drawer or sends a request,
   **Then** the drawer says the advisor is unavailable and why, and every other view keeps working.
5. **Given** the run fails or the connection drops, **When** that happens, **Then** the drawer shows
   the reason and lets the user try again; the chart keeps what was selected.
6. **Given** a run in progress, **When** the user cancels it, **Then** the run stops and the drawer
   says it was cancelled.

---

### User Story 6 - Run the whole stack with one command (Priority: P1)

A maintainer, or anyone who clones the repository, runs one command and gets the web page, the
REST API, the MCP server and the advisor on one port, with the search models and the index inside.
The container stays within a fixed memory budget, which is measured and recorded. The advisor's
public address in its agent card can be set for where the container is deployed. The README
explains how to run it locally and how the same image would run on a managed container service,
without deploying it.

**Why this priority**: The constitution requires one-command startup (Principle V), and the
milestone is the full stack running anywhere.

**Independent Test**: On a clean checkout with the local data built, run the one command, open the
page, run a search in both modes, check eligibility, fetch the agent card and call an MCP tool, all
on the one port; record the container's peak memory.

**Acceptance Scenarios**:

1. **Given** a clean checkout and the built index, **When** the maintainer runs the one command,
   **Then** the page, `/api/v1`, `/mcp`, `/a2a` and the agent card all answer on one port, and no
   other service is started.
2. **Given** the running container, **When** the accurate search runs on a pasted ad, **Then** the
   container's memory stays within the configured limit, and the measured peak is recorded in the
   repository.
3. **Given** a public address is configured, **When** a client fetches the agent card, **Then** the
   card's interface URL is that address; with nothing configured it is the local address.
4. **Given** the container has no model key, **When** it starts, **Then** everything except the
   advisor works, and the advisor reports that it is unavailable.
5. **Given** the README, **When** a reader follows it, **Then** it gives the local command, the
   environment variables (model key, model name, public address, store location) and the steps for
   a managed container service, and it states that the managed deployment has not been done.

---

### Edge Cases

- **Out-of-order search answers**: a slow answer for older text arrives after a fast answer for
  newer text. The page shows only answers for the current text.
- **Empty or whitespace query**: no search is sent and the results area explains what to type.
- **Very long paste**: text above the API's length limit is refused before sending, with the limit
  stated.
- **A code with no salary data at all**: the chart shows the code's row with a note instead of a
  bar, and its threshold line is still drawn.
- **A code that is banned**: the chart and comparison show that permits cannot be granted for it,
  with the source; no floor line is drawn for it.
- **Duplicate selection**: selecting a code already on the chart does nothing and says so.
- **Advisor selects more than four codes**: the chart keeps the four most recently looked-up codes
  and the drawer says which were left out.
- **The server restarts mid-run**: the drawer reports a lost connection and offers to retry.
- **Narrow screens**: every view works at phone width with no sideways page scroll; the chart
  stacks its labels rather than shrinking text below a readable size.
- **Stale median**: after the yearly median update date, if the registry has not been updated, the
  page shows the stale-median warning that the API returns.

## Requirements *(mandatory)*

### Functional Requirements

**Search**

- **FR-001**: The page MUST run the fast search as the user types, and the accurate search once
  the user pauses, and MUST show which of the two produced the list on screen.
- **FR-002**: The page MUST discard any search answer that is not for the text currently in the
  box.
- **FR-003**: For a pasted job ad, the page MUST show each passage as kept or set aside with the
  reason, and the text the search used, all as returned by the API's ad parsing.
- **FR-004**: Each result MUST show the code, the Swedish and English titles, the matched passage,
  the legal flags with sources, and one rank per search method, with methods that did not run shown
  as not run.
- **FR-005**: When the accurate search is unavailable, the page MUST keep the fast results and
  show the reason the API gives.

**Salary chart**

- **FR-006**: The chart MUST show up to four codes, each with a 10th–90th percentile bar, the
  median, a shaded 10th–25th percentile band, age-band mean dots and its applicable floor line
  labelled with rule and amount.
- **FR-007**: Every value on the chart MUST come from the API's salary payload; the page MUST NOT
  compute, interpolate or fill in any salary figure, and MUST show a suppressed value as missing
  with a note.
- **FR-008**: A simulated age-adjusted bar MUST be off by default, switchable per code and age
  band, visually distinct from official data, labelled simulated, and show its formula and inputs
  on request.
- **FR-009**: The chart MUST name the SCB table and reference year it was drawn from, and credit
  the data sources as the data dictionary requires.
- **FR-010**: The chart's figures MUST also be available as an accessible table, and every mark's
  exact value MUST be reachable by keyboard and touch as well as by pointer.

**Comparison**

- **FR-011**: The compare view MUST show, for two to five codes, the official task text with its
  source, the salary summary, threshold, flags and, when an offer is entered, the eligibility
  result per code, all as returned by the API's compare operation.
- **FR-012**: The compare view and the search results MUST show the honest-fit notice, and MUST
  NOT order, highlight or word results so as to suggest choosing a code for its lower threshold.

**Legal guide and calculator**

- **FR-013**: The legal guide MUST show the rules, the timeline of medians and rule changes, the
  exempt and banned codes and the transition rule, with every figure and date taken from the API
  and every statement linked to its source with its checked-on date.
- **FR-014**: The calculator MUST take an offer and a code and show the API's eligibility answer:
  status, rule, threshold, margin, warnings with sources, and the disclaimer.
- **FR-015**: The calculator MUST show validation errors per field in plain words.
- **FR-016**: Every view that shows a legal conclusion MUST state that it is information, not legal
  advice.

**Advisor drawer**

- **FR-017**: The drawer MUST send the user's ad, background and optional offer to the advisor and
  show its progress, results and memo as they stream in.
- **FR-018**: When the advisor publishes a salary or comparison result, the page MUST select those
  codes on the chart within the four-code limit and draw the chart from that result's data.
- **FR-019**: Before the first send, the drawer MUST tell the user that the message goes to a
  third-party model service.
- **FR-020**: When the advisor is unavailable, fails or is cancelled, the drawer MUST say so with
  the reason, and the rest of the page MUST keep working.
- **FR-021**: The user MUST be able to cancel a run in progress.

**General**

- **FR-022**: The page MUST be in English, with Swedish SSYK titles and legal terms shown next to
  their English equivalents.
- **FR-023**: The page MUST work at phone and desktop widths with no sideways page scroll.
- **FR-024**: The page MUST NOT store the user's ad, background or offer anywhere but the
  browser's memory for the current visit, and MUST NOT send them anywhere but this server.
- **FR-025**: The page MUST call the API through types generated from the API's own schema, so a
  field change in the API breaks the page's build rather than its behaviour.

**Packaging and deployment**

- **FR-026**: One command MUST build and start the page, REST, MCP and the advisor on one port,
  with the search models and index available, and no other services.
- **FR-027**: The container's memory MUST be capped at the budget set by the maintainer, and its
  measured peak during an accurate search MUST be recorded in the repository.
- **FR-028**: The advisor's public address in its agent card MUST be settable by configuration,
  defaulting to the local address.
- **FR-029**: The container MUST start and serve everything except the advisor when no model key
  is given.
- **FR-030**: The model key MUST reach the container only at run time, never inside the image.
- **FR-031**: The README MUST document the local run, every environment variable, and the managed
  container-service variant, marked as not deployed.

### Key Entities

- **Search session**: the text in the box, the latest answer for each search speed, and which one
  is on screen. Lives only in the page.
- **Selection**: the ordered set of up to four codes on the chart (up to five for comparison), each
  with its salary payload and its simulated-bar setting. Updated by the user and by the advisor.
- **Offer draft**: the calculator's and drawer's offer fields, validated by the API's eligibility
  model.
- **Advisor run**: one request to the advisor and the events it streams (progress, structured
  results, memo, final state).
- **Deployment settings**: the model key, model name, public address and store location that the
  container reads at start-up.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: While typing, the result list reflects the current text within 0.5 seconds of each
  keystroke on the reference machine.
- **SC-002**: For a pasted ad of about 600 words, the accurate ranking appears within 3 seconds of
  the user's pause on the reference machine, with the accurate model loaded.
- **SC-003**: An English job ad and its Swedish translation give the same top three codes, in any
  order, through the page.
- **SC-004**: 100 % of the salary, threshold and legal figures shown in the page match the API's
  response for the same input, as checked by automated tests of each view.
- **SC-005**: All three main views (search with chart, compare, legal guide with calculator) are
  usable at 390 px and 1280 px wide with no sideways scroll, shown by screenshots at both widths.
- **SC-006**: From a clean checkout with the index built, the one command serves the page within
  10 minutes of build time and 60 seconds of start-up on the reference machine.
- **SC-007**: The container's peak memory during an accurate search on a pasted ad stays under the
  configured limit, and is recorded.
- **SC-008**: With the advisor on, the chart's selection changes during the run, before the memo
  arrives, in a recorded end-to-end run.
- **SC-009**: The page passes an automated accessibility check with no serious or critical
  violations on each main view.

## Assumptions

- The reference machine is the maintainer's laptop (Apple M2 Pro, 16 GB), as in Features 001–003.
- The memory budget is 4 GB, as the maintainer set in Feature 001.
- The search index and processed data are built locally with `lonekrav-etl` before the container
  is built; the container does not run the data pipeline, which takes over an hour cold.
- The page is served by the same server as the API, so there is no cross-origin setup and no
  login; Lönekrav has no user accounts.
- The applicable floor line on the chart is the one for a first permit decided today, unless the
  user has entered an offer, in which case it follows the offer's application type and dates.
- The end-to-end check uses a real public job ad and a translation of it. Only the ad's source
  link and the resulting codes are committed as evidence, not the ad text.
- The managed container-service variant is documented only; no cloud account is used.
- Fast search accuracy on long full sentences is a known limitation from Feature 003; the accurate
  search on pause is the remedy, and this feature does not change search ranking.
