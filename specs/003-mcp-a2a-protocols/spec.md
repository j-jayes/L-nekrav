# Feature Specification: Lönekrav over MCP and A2A

**Feature Branch**: `003-mcp-a2a-protocols`

**Created**: 2026-10-22

**Status**: Draft

**Input**: User description: "003-mcp-a2a-protocols: serve Lönekrav's existing core functions over
two more protocols, mounted on the same FastAPI app as /api/v1, so a chat model can use them.
(1) MCP server at /mcp (FastMCP, mounted via mcp.http_app()): tools search_occupations (fast or
full, optional parse_ad), extract_job_ad_signal, get_occupation_salary (optional age band and date),
evaluate_permit_eligibility, compare_occupations; resources legal://timeline and ssyk://{code};
every tool returns the same pydantic models as the REST routes, including honest-fit text, sources
and checked-on dates. (2) A2A agent lonekrav-advisor at /a2a (a2a-sdk, A2A v1.0): discoverable at
/.well-known/agent-card.json; accepts a job ad, the applicant's background and the offer; streams
status updates, tool-call artifacts (structured ui_sync parts so a UI can update its charts), and a
final memo in the honest-fit voice: it shows every plausible code and its consequences, and never
advises picking a code that doesn't match the real duties. The agent runs an OpenAI-compatible tool
loop against OpenRouter (OPENROUTER_KEY, model from LONEKRAV_LLM_MODEL, defaulting to a cheap, fast
model). It binds the same core functions as MCP. Requirements: adapters stay thin (Principle I): no
logic in protocols/. Without OPENROUTER_KEY, MCP and /api/v1 work fully, and /a2a answers with a
clear 'agent unavailable' message instead of failing (Principle V). Unit tests run the agent
executor against a fake model client; one live smoke test is skipped when the key is absent.
Evidence, saved to references/: add the MCP server to Claude Code and call a tool from it, saving the
transcript; fetch the agent card, then run a streamed message call with the A2A client printing its
events, saving that transcript."

## Clarifications

### Session 2026-10-22

- Q: How should the advisor handle the personal data it sends to a third-party model service? → A:
  Send it unchanged, and disclose this in the agent card and in the memo footer. Request contents
  are still never logged.
- Q: In what form does a client send the advisor its input? → A: As a structured data part (ad,
  background, offer), with the offer validated against the eligibility model. Plain text is also
  accepted, and the model then reads the offer out of it.
- Q: Should the advisor support follow-up messages in the same conversation? → A: No. Each message
  is one independent run that produces one memo; a follow-up is a new task, and the client resends
  the context.

## User Scenarios & Testing *(mandatory)*

Feature 002 answers the work-permit questions (which codes fit a job, what each code's salary
requirement is, whether an offer passes) over a REST API. The people who benefit from 003 are the
same job seekers and advisers, but they reach Lönekrav through a chat assistant rather than a web
form. There are two kinds of direct consumer:

- **A chat assistant acting as a client** (for example Claude Code or Claude Desktop). It calls
  Lönekrav's operations one at a time and composes its own answer from the results.
- **A user interface or another agent that wants a finished answer**. It hands Lönekrav's own
  advisor the job ad, the applicant's background and the offer. While the advisor works it receives
  progress and the intermediate results, and at the end it receives a memo. The 004 web client's
  chat drawer is the first planned UI of this kind.

### User Story 1 - A chat assistant uses Lönekrav's operations (Priority: P1)

A user adds Lönekrav to their chat assistant as a tool server. They ask a question such as "which
SSYK codes fit this ad and what salary would each need?". The assistant finds Lönekrav's operations
(search occupations, extract the job-describing parts of an ad, get a code's salary picture, check
an offer's eligibility, compare codes), calls them, and gets the same answers the REST API gives:
the honest-fit notice, sources, table references and checked-on dates. The assistant can also read
the legal timeline and any occupation's profile as reference documents.

**Why this priority**: This is the cheapest way to put Lönekrav inside a chat model. It has no
model costs and no key, and every answer comes straight from the already-tested core.

**Independent Test**: Start the server, connect a tool-calling chat client to it, list the
operations and documents, call each operation, and compare each result with the matching REST
response for the same input.

**Acceptance Scenarios**:

1. **Given** a running server, **When** a client lists the tools, **Then** it sees exactly the
   five operations. Each one has a description and an input schema that a model can use without
   further documentation.
2. **Given** an English job-ad text, **When** the client calls search in fast mode with ad parsing
   on, **Then** the result equals the REST search response for the same request, including the
   honest-fit text.
3. **Given** a known code, an age band and a date, **When** the client asks for the salary picture,
   **Then** it gets the same payload as the REST salary route: source table, reference year, the
   applicable threshold and any simulated figures marked as simulated.
4. **Given** an offer, **When** the client checks eligibility, **Then** it gets the same answer as
   REST: the rule, threshold, pass or fail, margin, warnings with sources and checked-on dates, and
   the disclaimer.
5. **Given** two to five codes, **When** the client compares them, **Then** it gets the same
   comparison as REST, including official task texts and the honest-fit text.
6. **Given** a client, **When** it reads the legal timeline document or a code's profile document,
   **Then** the timeline equals the REST timeline. The profile equals the REST occupation response
   and carries no ILO text.
7. **Given** an unknown code or invalid input, **When** any tool is called, **Then** the client gets
   a tool error naming the problem, as REST returns 404 or 422. The server keeps running.

---

### User Story 2 - An advisor agent writes an honest-fit memo (Priority: P2)

A UI or another agent sends Lönekrav's advisor a job ad, a short description of the applicant's
background and the offer (salary, share of full time, application type and dates). The advisor
reports progress as it works ("reading the ad", "searching occupations", "checking eligibility").
Each time it calls one of Lönekrav's operations, it publishes the result as a structured item the
UI can use directly, for example to draw a code's salary distribution or select codes on a chart.
It finishes with a memo. The memo lists every plausible code with the consequences of each
(threshold, pass or fail, warnings) and states that the code must match the real duties. It never
recommends a code because its threshold is lower.

**Why this priority**: The advisor is the showcase of the feature and the backend for the 004 chat
drawer. It depends on the same operations as Story 1, and it needs a paid model key, so it comes
second.

**Independent Test**: Run the advisor against a scripted fake model that requests a fixed sequence
of operations. Check the order and content of the streamed events and the final memo. Separately,
run one real request with the key present and save the transcript.

**Acceptance Scenarios**:

1. **Given** a running server, **When** a client fetches the well-known agent card, **Then** the
   card names the agent `lonekrav-advisor`, says it streams, and describes its one skill and the
   input it expects.
2. **Given** an ad, a background and an offer, **When** the client sends a streamed message,
   **Then** it receives, in order: a "working" status, one or more progress statuses, one
   structured result item per operation the advisor called, the memo, and a "completed" status.
3. **Given** each structured result item, **When** the UI reads it, **Then** it can tell which
   operation produced it, read the codes involved, and find the same data the operation returns
   (for example the salary payload a chart is drawn from).
4. **Given** an ad that fits two codes with different thresholds, **When** the memo is written,
   **Then** it presents both codes and their consequences. It states that the choice must follow
   the real duties, and it contains no advice to pick the code with the lower threshold.
5. **Given** the memo, **When** it mentions any threshold, median or legal date, **Then** that
   figure came from an operation result in the same run and was not written by the model on its
   own. The memo cites the source and checked-on date of the legal statements it relies on.
6. **Given** the model asks for an operation with invalid arguments, **When** the advisor runs it,
   **Then** the model receives the error text, and the run either recovers or ends with a "failed"
   status that explains why. It never hangs.

---

### User Story 3 - Lönekrav still works without a model key (Priority: P3)

Someone runs Lönekrav without an OpenRouter key: a reviewer, CI, or someone who does not want to
pay for a model. Everything except the advisor works normally. The advisor is still discoverable,
but a message to it gets a clear "agent unavailable: no model key configured" answer instead of an
error or a hang.

**Why this priority**: Principle V requires it. It is small, but it decides whether the server
starts at all on a fresh machine.

**Independent Test**: Start the server with the key unset. Call /api/v1 and the tool server, which
must work, then send the advisor a message and check the answer.

**Acceptance Scenarios**:

1. **Given** no key, **When** the server starts, **Then** it starts without error, and the REST
   routes and the tool server answer as in Story 1.
2. **Given** no key, **When** a client fetches the agent card, **Then** the card is served.
3. **Given** no key, **When** a client sends the advisor a message, **Then** the task ends promptly
   in a terminal state with a message that says the agent is unavailable and why.

---

### Edge Cases

- The model never stops calling tools: the advisor stops after a fixed maximum number of tool
  rounds and finishes with a failed status that says so.
- The model service is down, slow or returns an error: the run ends with a failed status naming
  the cause. It never hangs, and the server stays up.
- The model replies in plain text without calling any operation: the advisor still has to report
  results honestly. A memo that rests on no operation result is not passed off as Lönekrav's
  answer (see FR-016).
- The job ad is empty or longer than the REST limit: the input is rejected the same way REST
  rejects it.
- The background or offer is missing: the advisor works from what it has. With no offer it does
  not check eligibility and says so in the memo.
- Full-mode search cannot load its large model: the fallback to fast mode is reported in the
  result, as in REST.
- Two advisor requests run at once: both complete. Lazily created shared resources (the model
  client) are created once without races.
- A client cancels a streamed task: the run stops, any model call in flight is abandoned and its
  result discarded, and the task ends in a cancelled state.

## Requirements *(mandatory)*

### Functional Requirements

**Shared**

- **FR-001**: The tool server and the advisor MUST be served by the same application, and on the
  same port, as the existing REST API. The REST API's behaviour MUST NOT change; its existing
  tests and the recorded responses in `references/api-smoke.md` remain the reference.
- **FR-002**: Any rule the REST adapter applies today beyond validation and serialisation (an
  unknown code becomes "not found", ILO text is stripped from profiles, the salary date defaults to
  today, code titles are supplied to the salary payload) MUST move to one shared place outside the
  protocol adapters. REST, the tool server and the advisor MUST all use it, so that no protocol
  adapter contains domain logic.
- **FR-003**: Every operation result over every protocol MUST be the same data model the REST API
  returns for the same input. Its honest-fit text, sources, table references and checked-on dates
  MUST NOT be removed or reworded.
- **FR-004**: No legal amount, percentage or date may appear in the new adapters, the advisor's
  instructions or the tests, except through the legal registry. The existing registry-leak test
  MUST cover the new code.
- **FR-005**: As with REST, logs MUST record only the method, path, status and duration of each
  request. They MUST NOT record ad text, background, offers or model messages. This applies to
  every new log source: the tool server, the A2A library, the advisor loop and the model client.
  Texts that leave the caller's own exchange MUST NOT echo request content. These are the A2A
  failed-state message and any error passed to the third-party model. They name the field and the
  rule, not the value. A REST 422 or an MCP tool error returned to the same caller may echo that
  caller's own input, as REST does today (FR-001).

**Tool server (MCP)**

- **FR-006**: The tool server MUST offer exactly five tools: `search_occupations` (text, fast or
  full mode, number of results, optional ad parsing), `extract_job_ad_signal` (ad text),
  `get_occupation_salary` (code, optional age band, optional date), `evaluate_permit_eligibility`
  (the same fields as the REST eligibility request) and `compare_occupations` (two to five codes and
  an optional offer, as in REST).
- **FR-007**: The tool server MUST offer two read-only resources: `legal://timeline` (the legal
  timeline) and `ssyk://{code}` (an occupation profile with its legal flags and without ILO
  text).
- **FR-008**: Each tool's input schema and description MUST be generated from the same models
  and constraints as REST (for example the 20 000-character ad limit, and two to five codes), so
  that invalid input is rejected with the same rules.
- **FR-009**: An unknown code, an unknown age band or invalid input MUST produce a tool error that
  names the problem. It MUST NOT produce an empty result or crash the server.

**Advisor (A2A)**

- **FR-010**: The advisor MUST be discoverable at the standard well-known agent-card path. The
  card MUST give its name (`lonekrav-advisor`), a description, that it supports streaming, its
  single skill (an honest-fit occupation and salary memo), and its expected input.
- **FR-011**: The advisor MUST accept a job ad, an applicant background and an offer in one of two
  forms. The preferred form is a structured data part with the fields `ad`, `background` and
  `offer`. Its offer is validated against the same model as the REST eligibility request, and
  invalid input ends the task as failed, with the validation message, before any model call.
  Plain text is also accepted: the model reads the offer out of it, and the eligibility tool then
  validates those arguments. The background and the offer are optional in both forms.
- **FR-011a**: Each message MUST be one independent run. Messages MUST NOT carry conversation
  history between tasks, even when they share a context identifier.
- **FR-012**: A streamed request MUST deliver: status updates while the advisor works; one
  structured result item per operation call (a `ui_sync` item naming the operation, its arguments
  and its full result); a final memo; and a terminal status (completed, failed, rejected or
  cancelled). A failed operation call produces no `ui_sync` item: its error text goes back to the
  model, and the progress status says the call failed. A non-streamed request MUST return the same
  final task.
- **FR-013**: The advisor MUST run a tool loop against an OpenAI-compatible chat model. Its tools
  MUST be the same five operations as the tool server, with the same schemas, backed by the same
  shared functions.
- **FR-014**: The model MUST be chosen with one environment setting. Without that setting it MUST
  default to a cheap, fast model that supports tool calls. The key MUST be read only from the
  environment or `.env`. It MUST NOT be logged or returned.
- **FR-015**: The loop MUST stop after 8 model rounds. Each model call MUST time out after 30
  seconds and be retried at most once. When either limit is hit, the run MUST end with a failed
  status that explains why. If the model sends tool arguments that are not valid JSON, the parse
  error MUST go back to the model as that call's error, as for any other invalid input.
- **FR-016**: The advisor's instructions and memo MUST follow Principle III: show every plausible
  code with its consequences, state that the code must match the real duties, never suggest a code
  for its lower threshold, cite the legal sources and checked-on dates from operation results,
  and say that it is information, not legal advice. The memo MUST end with a footer that says the
  input was processed by a third-party model service. If the model's memo does not contain
  the core honest-fit text verbatim, or no operation was called, the advisor MUST add the honest-fit and
  disclaimer text from the core models itself rather than trust the model.
- **FR-017**: Without a model key the advisor MUST stay discoverable. A message to it MUST end
  within one second in the rejected state whose text says the agent is unavailable because no model key is
  configured. All other surfaces MUST be unaffected.
- **FR-018**: Shared resources created lazily, such as the model client, MUST be created
  thread-safely, as the Harrier model is in 002.

**Testing and evidence**

- **FR-019**: Every tool and resource MUST have tests that run with no server process and no
  network, against the existing test fixtures. Each test MUST check that the result equals the
  REST response for the same input.
- **FR-020**: The advisor MUST be tested against a scripted fake model client. The tests MUST cover
  event order, `ui_sync` content, the honest-fit guard (FR-016), the round limit, model errors and
  the no-key path. One live test MUST call the real model and MUST be skipped when the key is
  absent.
- **FR-021**: Two transcripts MUST be saved under `references/`: (a) the tool server added to Claude
  Code and a tool called from it; (b) the agent card fetched, then a streamed advisor message (`SendStreamingMessage`, the A2A v1.0 name of the handoff's `message/stream`) with
  its events printed by the A2A client. Each transcript MUST also record how long the call took.

### Key Entities

- **Tool**: one of the five named operations. It has an input schema derived from the core request
  models and returns a core result model.
- **Resource**: a read-only document addressed by a URI: the legal timeline, or one occupation
  profile.
- **Agent card**: the advisor's public description: name, description (including the
  third-party model disclosure), version, capabilities (streaming), skill, input and output modes
  (structured data and text), and the endpoint URL.
- **Advisor request**: a job ad (required), the applicant's background (optional) and an offer
  (optional, with the eligibility request's fields).
- **Task and events**: one advisor run. It emits status updates, `ui_sync` result items
  (operation name, arguments, result) and the memo, and ends in a terminal state.
- **Memo**: the final text, in the honest-fit voice. It lists the plausible codes and their
  consequences, the sources and checked-on dates, the duties requirement, and the not-legal-advice
  statement.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every tool and resource, the result for each tested input is identical to the
  REST response for the same input (100 % of compared cases).
- **SC-002**: A user can connect Claude Code to a running Lönekrav with one command and get a
  correct answer from a Lönekrav tool on the first try. The saved transcript shows this.
- **SC-003**: In 100 % of scripted advisor runs, events arrive in the specified order, there is one
  `ui_sync` item per operation call, and the run ends in a terminal state.
- **SC-004**: No advisor memo in the tests or the saved transcript recommends a code for a lower
  threshold. Every memo states the duties requirement and the not-legal-advice notice.
- **SC-005**: With the key absent, the full default test suite passes. The REST API and the tool
  server answer, and the advisor ends a message with the unavailable notice in under one second.
- **SC-006**: A live advisor run on a typical ad (about 300 words, with an offer) completes, and
  its total time and model-time share are recorded in `references/`. There is no target yet; this
  measurement sets the baseline for the 004 chat drawer.
- **SC-007**: All existing tests (264 default, 9 benchmark) still pass.

## Assumptions

- The tool server and the advisor have no authentication, like `/api/v1`. They are meant for a
  local or single-tenant deployment. Authentication belongs to a later deployment feature.
- The advisor sends the ad, background and offer to a third-party model service (OpenRouter)
  unchanged (Clarifications). The agent card's description and the memo footer (FR-016) say so.
- An advisor run is single-turn (FR-011a). Follow-up questions, conversation memory and an "input
  required" step are out of scope; 004 can add them if the chat drawer needs them.
- Task state is kept in memory and lost on restart, which is acceptable for a single-process
  deployment.
- The advisor writes the memo in English. Swedish SSYK titles and legal terms are shown alongside,
  as in the rest of the UI.
- The default model is chosen in planning by checking price, tool-call support and latency on
  OpenRouter. The choice is recorded together with the date it was checked.
- The protocol library versions are pinned in planning after checking them against the package index
  (fastmcp 4.1.3 is current; the development plan named 4.1.2).
