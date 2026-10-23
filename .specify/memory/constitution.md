<!--
Sync Impact Report
- Version change: 1.0.1 → 1.0.2 (PATCH, 2026-10-23): Technology and Data Constraints lists the
  Feature 005 sources: Arbetsförmedlingen's JobSearch and historical ads APIs (CC0) and SCB
  TAB5696 (mean salary by national area). No principle changes. Templates: no edits required.
- Earlier: 1.0.0 → 1.0.1 (PATCH, 2026-10-20): Principle IV clarifies that the
  cross-lingual benchmark runs under a `benchmark` marker and gates merges of data or search changes,
  rather than running in every default test run. Prompted by the Feature 001 clarification and the
  /speckit-analyze finding D1.
- Earlier: (template) → 1.0.0
- Principles defined: I. Core First, Adapters Thin; II. Data Integrity; III. Honest Fit;
  IV. Test-First and Proven by Hand; V. Compact and Portable; VI. Simplicity and Surgical Change
- Added sections: Technology and Data Constraints; Development Workflow; Governance
- Removed sections: none
- Templates checked: plan-template.md (Constitution Check gate reads principles from this file),
  spec-template.md, tasks-template.md: no edits required
- Deferred TODOs: none
-->

# Lönekrav Constitution

## Core Principles

### I. Core First, Adapters Thin

- All domain logic (SSYK taxonomy, SCB salary transforms, legal thresholds, eligibility,
  job-ad signal extraction, embedding and vector search) MUST live in `src/lonekrav/core/`.
- `core` MUST NOT import FastAPI, FastMCP, a2a-sdk or any other transport framework. Every core
  function MUST be callable from a pytest with no server running.
- The three protocol surfaces — `/api/v1` (FastAPI REST and SSE), `/mcp` (FastMCP) and `/a2a`
  (A2A v1.0 via `a2a-sdk`) — MUST only validate input, call core and serialise output.
- All surfaces MUST share one set of pydantic v2 models. A new field is added once, in core.

Rationale: the project's showcase is one domain served over several protocols. Logic that leaks
into an adapter has to be rewritten for each of the others and drifts.

### II. Data Integrity (NON-NEGOTIABLE)

- SCB salary figures MUST NOT be fabricated, imputed or silently interpolated. A suppressed or
  missing SCB cell stays `null` end to end and the UI says so.
- Every salary payload MUST carry `source_table`, `reference_year` and `fetched_at`.
- Any derived number (for example age-adjusted quantiles) MUST carry `is_simulated: true` and
  the formula used, and MUST be visually distinct from official figures.
- Legal thresholds and rules MUST live only in the `LegalConstants` registry. Each row MUST have
  an effective-from date, an optional effective-to date, and a source URL. No threshold literal
  may appear anywhere else in code, copy or tests except tests of the registry itself.
- Every external dataset MUST be recorded in `data/processed/data-dict.yaml` with provenance,
  licence and attribution.

Rationale: users make visa and salary decisions from these numbers. A plausible wrong number is
worse than an honest gap.

### III. Honest Fit

- Occupation comparison MUST show, for each plausible SSYK code, its salary consequences and its
  official SCB task description, and MUST state that the code has to match the actual duties.
- Copy, agent prompts and agent output MUST NOT advise choosing a code that does not fit the
  duties in order to lower a salary threshold.
- Every legal statement shown to users MUST link its source and show a checked-on date, and the
  product MUST state that it is information, not legal advice.

Rationale: the union statement (yttrande) and Migrationsverket check duties against the code.
Misclassification hurts the applicant; transparency helps them negotiate.

### IV. Test-First and Proven by Hand (NON-NEGOTIABLE)

- Red/green TDD: a test MUST be written and seen to fail for the right reason before the code
  that makes it pass.
- A change is not done until it has been run for real — CLI on a fixture, `curl` against a dev
  server, or a browser screenshot — and that evidence is in the pull request.
- A bug found by hand MUST be fixed by first writing a failing regression test.
- Retrieval quality is a tested property: the cross-lingual benchmark MUST live in the test suite
  under the `benchmark` marker, MUST fail when its headline metrics regress, and MUST pass before
  any change to data or search is merged. The default test run stays fast and offline.

Rationale: passing unit tests do not prove that a server boots or that an English query finds
the same occupation as its Swedish translation.

### V. Compact and Portable

- `docker compose up --build` MUST start the whole stack (API, MCP, A2A, static frontend) on one
  port with no other services.
- The container memory budget MUST be measured, recorded in `references/`, and enforced with
  `mem_limit` in compose.
- Milvus Lite (a local file) is the default store; setting `MILVUS_URI` MUST be the only change
  needed to use a Milvus server.
- Anything that needs `OPENROUTER_KEY` MUST degrade gracefully, with a clear message, when the
  key is absent. Data pipelines MUST NOT depend on an LLM for required fields.

Rationale: the stack must run on an old laptop as well as on Cloud Run.

### VI. Simplicity and Surgical Change

- No features, abstractions or configurability beyond what a spec asks for. No error handling
  for impossible scenarios.
- Every changed line MUST trace to the current spec or task. Adjacent code, comments and
  formatting are left alone; dead code found along the way is reported, not removed.
- If an implementation could be a quarter of its size, it MUST be rewritten before review.

Rationale: an agent-built codebase grows by accretion unless size is treated as a defect.

## Technology and Data Constraints

- Backend: Python 3.12 managed with `uv`; pydantic v2 at every boundary; `ruff` for lint and
  format; `pytest` for tests. Embeddings via `sentence-transformers` with
  `KBLab/sentence-bert-swedish-cased` and `microsoft/harrier-oss-v1-0.6b`; vector store
  `pymilvus` with Milvus Lite; BM25 through Milvus functions.
- Frontend: React 19, TypeScript, Vite and Tailwind. The UI is English; Swedish SSYK titles and
  legal terms are shown alongside so users can copy them into forms.
- Data sources: SCB PxWeb v2 (TAB5932 percentiles, TAB5844 age-band means), SCB SSYK 2012
  structure, English titles, title index and ISCO key; JobTech Taxonomy; ILO ISCO-08
  definitions; ESCO; SCB TAB5696 (mean salary by national area); Arbetsförmedlingen's JobSearch
  and historical ads APIs (ad counts only, CC0). Raw downloads are cached under `data/raw/` and never committed.
- Secrets live only in `.env`, which is gitignored. No secret may appear in logs, fixtures or
  committed artefacts.

## Development Workflow

- One spec-kit cycle per feature: specify, clarify, plan, checklist, tasks, analyze,
  implement, converge — on branch `NNN-short-name`.
- One pull request per feature, split further where natural. Every PR includes the commands run
  and their output, and screenshots for visual changes. The author reads every line before
  opening it, including the description.
- Each session starts by running `uv run pytest` and reading recent history.
- Each feature ends with a linear walkthrough in `docs/walkthroughs/` (snippets emitted from
  disk, never retyped) and a compound step that saves reusable working examples to
  `references/` or folds new rules into `CLAUDE.md`.

## Governance

- This constitution supersedes other practice in this repository. `CLAUDE.md` holds runtime
  guidance and MUST NOT contradict it.
- Amendments are made through `/speckit-constitution`, recorded in the Sync Impact Report, and
  committed on their own.
- Versioning: MAJOR for removing or redefining a principle, MINOR for a new principle or
  materially expanded guidance, PATCH for wording.
- Every plan's Constitution Check gate and every PR review MUST confirm compliance. Any
  deviation is recorded in the plan's Complexity Tracking table with its justification.
- The `LegalConstants` registry MUST be reviewed every June when SCB publishes a new median, and
  whenever Migrationsverket announces a rule change.

**Version**: 1.0.2 | **Ratified**: 2026-10-20 | **Last Amended**: 2026-10-23
