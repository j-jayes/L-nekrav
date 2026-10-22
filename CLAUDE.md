## Core engineering standards

### 1. Think Before Coding

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

- No features beyond what was asked. No abstractions for single-use code.
- No configurability that wasn't requested. No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.
- The test: would a senior engineer say this is overcomplicated?

### 3. Surgical Changes

- Don't 'improve' adjacent code, comments, or formatting. Match existing style even if you'd do it differently.
- Remove imports and variables that YOUR change orphaned. Leave pre-existing dead code alone — mention it instead.
- The test: every changed line must trace directly to the request.

### 4. Goal-Driven Execution

- Turn the task into a verifiable goal before starting. 'Fix the bug' becomes 'write a test that reproduces it, then make it pass'.
- For multi-step work, state the plan as `step -> verify:` pairs.
- Weak criteria ('make it work') force constant clarification. Strong criteria let you loop unattended.

### 5. Execute Before You Claim

- Never assume code works until it has been executed. Passing tests are not proof it works — a server that won't boot passes every unit test.
- Always give yourself a validation mechanism: a dev server, a fixture file, a known-good output to diff against.
- Red before green. Confirm the new test FAILS before implementing, or you may be testing nothing.
- A bug found by hand gets fixed via red/green TDD, so it becomes a permanent regression test.

### 6. Don't Inflict Unreviewed Code

- Never open a PR containing code you have not read yourself. The first review pass is your job, not the reviewer's.
- Several small PRs beat one big one. Splitting commits is cheap when an agent does the git work.
- Review the PR description too — agents write convincing ones that are wrong.
- Include evidence: how you tested it, why you chose this implementation, screenshots if it's visual.

### 7. Hoard What You Know How To Do

- A trick only has to be worked out once. Save the working example to `references/` and point future agents at it.
- Prefer 'build X by combining these two working examples' over describing the mechanics from scratch.
- 'Similar to how `<existing thing>` works' replaces a spec. Clone a reference repo to a temp dir rather than paraphrasing it.
- End a task with the compound step: fold what you learned back into this YAML or a skill. Small improvements compound.

### 8. Work With The Grain Of The Harness

- Fetch raw source with `curl`, not a summarising fetch tool, when you need the actual bytes.
- Scratch work goes in a temp directory so it can never be committed by accident.
- Never retype code into a document — emit it by running `cat`/`sed`/`grep` so it cannot be hallucinated.
- A subagent must justify itself on token economics, not role-play. Fan out only over genuinely independent work.

## Definition of done

A change is not finished until:

- It works, and you have *seen* it work.
- It solves the right problem — the one that was actually asked.
- Failure paths are handled, and errors say enough to debug them.
- It is the minimum code that does the job.
- Tests cover it, and they failed before the implementation existed.
- Docs that the change invalidated have been updated.
- It doesn't make the next change harder than it needs to be.

## Slides

The Nexer slide kit is installed in `slides/` (from
[j-jayes/slides](https://github.com/j-jayes/slides)). `slides/template.qmd` is a
working gallery of every slide archetype — copy it, do not start blank.

```bash
cd slides
cp template.qmd my-deck.qmd
quarto render my-deck.qmd    # branded HTML + editable .pptx
```

One render fills two directories: the site into `docs/` (which also holds this
project's Word deliverables) and the `.pptx` into `reports/` (gitignored — that
is what you send people). `##` is the kicker, `###` is the action title.

The writing skills come from the `slides@j-jayes` plugin, enabled for this repo
in `.claude/settings.json`: `/slides:nexer-slides` for branding and export,
`/slides:jonathan-slides` for structure, `/slides:viz-index` for charts,
`/slides:colleague-deck` for editing a client's .pptx from `input/`.
R is installed but off PATH — add `C:\Program Files\R\R-4.5.1\bin\x64` before rendering.

## Lönekrav

The SSYK and salary navigator for Swedish work permits. Plan and verified facts:
`references/development-plan.md`; process is spec-kit
(`/speckit-constitution` → `-specify` → `-clarify` → `-plan` → `-checklist` → `-tasks` → `-analyze`
→ `-implement` → `-converge`), one feature branch `NNN-name` and one PR per feature.

```bash
uv run pytest                 # the suite; run it first (first-run-the-tests skill)
uv run lonekrav-etl --help    # fetch | build | index | benchmark
uv run lonekrav-serve         # FastAPI: /api/v1, /mcp, /a2a, static frontend
```

Layout: `src/lonekrav/core/` (all domain logic, framework-free), `etl/`, `api/`, `protocols/`,
`frontend/`, `data/processed/` (committed artefacts + `data-dict.yaml`), `data/raw/` (ignored),
`tests/`, `references/` (working examples), `specs/` (spec-kit).

Rules that are specific to this project:

- Never fabricate or interpolate SCB figures. Nulls stay null; derived numbers carry
  `is_simulated: true`; every salary payload names its SCB table and reference year.
- Legal thresholds live only in the `LegalConstants` registry (`src/lonekrav/core/legal_constants.yaml`),
  each row with an effective date, a source URL and a checked-on date; a test fails if any of its
  amounts or dates appears in code. Current floor: 34 470 SEK (90 % of SCB median 38 300, from 16
  June 2026). Every June, add the new median there; a test fails from 23 June until you do.
- Framing is honest fit: show consequences of each plausible code, never advise picking a code that
  does not match the real duties.
- The OpenRouter key is `OPENROUTER_KEY` in `.env` (gitignored). Anything that needs it must be
  skippable without it.

Things worked out once (Feature 001) — reuse, don't rediscover:

- **Fixtures** come from `scripts/cut_fixtures.py`: real slices of every source, cut before any
  parser exists. Add a code to its `CODES` list rather than hand-writing fixture data.
- **Milvus Lite**: `references/milvus_lite_hybrid.py` is the working pattern. The `.db` path is a
  directory, not a file; BM25 distances come back negative (`core.store.bm25_score`).
- **Harrier must load in fp32 on CPU**; its bf16 checkpoint is ~10× slower
  (`references/embedding-benchmark.md`, regenerate with `lonekrav-etl measure-models`).
- **Live sources break in ways fixtures do not**: ESCO serves 404s and permanent 500s for some
  linked occupations; SCB's SSYK publication prints some codes with one space. Run the real
  `fetch` and `build` before trusting a parser, and turn each surprise into a test.
- **ILO ISCO-08 text is never committed** (ILO reserves reproduction rights); `attach_ilo` adds it
  at index time. Salary tables must credit Medlingsinstitutet (see `data/processed/data-dict.yaml`).
- **Data dictionary**: validate with `data-dict validate-data data/processed/data-dict.yaml`
  (install: `cargo install --locked --git https://github.com/tidyverse/data-dict data-dict-cli`).
- The shell condenses pytest output; use `rtk proxy uv run pytest -q` to see the summary line.

Things worked out in Feature 002:

- **Benchmark queries leak through inflections.** ESCO descriptions open with their own label in
  the plural ("business managers are…"), so an exact-match hold-out let 104 of 111 English queries
  through and inflated English by ~7 points. `etl.benchmark.phrase_in` allows three trailing word
  characters; use it for any new query set.
- **Choose search weights on one query set and confirm on another**: `references/fusion_weight_sweep.py`
  caches chunk hits once and re-fuses per weight in seconds. Results in
  `references/benchmark-diagnosis-002.md`.
- **Dense search in numpy, not Milvus Lite**: 0.5 ms against 26 ms for 9 551 chunks
  (`SearchEngine.search_dense`). Milvus Lite has no `query_iterator`; load vectors with paged `query`.
- **KBLab queries are faster on one torch thread, Harrier is slower** (`Spec.query_threads`);
  Harrier dominates full mode on long text, so search pasted ads with `parse_ad`
  (`references/search-latency.md`).
- **Milvus Lite locks its directory**: stop `lonekrav-serve` before running a script or the
  benchmark against the same index.
- **Do not `git commit -a` while a build runs**: it writes `data/processed/` as it goes.
- Every route, with real responses: `references/api-smoke.md` (regenerate with
  `scripts/api_smoke.py` against a running server).

Things worked out in Feature 003:

- **One service, three surfaces**: `core/service.py` holds the not-found check, ILO stripping and
  salary defaults. REST and MCP call it, and the advisor reaches it only through the MCP tools
  (`McpTools`, an in-memory `fastmcp.Client`), so no tool definition is duplicated.
- **FastMCP at exactly `/mcp`**: `app.mount("/", mcp.http_app(path="/mcp"))`, mounted last, with
  `combine_lifespans`. A root mount catches routes added after it, so tests that add probe routes
  must insert them before it. Working example: `references/fastmcp_mount.py`.
- **A2A v1.0 (a2a-sdk 1.2.3)**: the streaming method is `SendStreamingMessage` (`message/stream` is
  the 0.3 name). The executor must enqueue the Task before any status update. Data parts are
  protobuf, so integers arrive as floats. With no key, tasks end `rejected`. Working example:
  `references/a2a_server_client.py`.
- **Libraries log bodies at DEBUG**: fastmcp (tool arguments), a2a (requests) and sse_starlette
  (every chunk). `create_app` pins them to INFO or above (`CONTENT_LOGGERS`). fastmcp does not
  propagate to root, so turn propagation on in any caplog test of it.
- **Small models send object arguments as JSON text**, with a stray brace. `loop._decode_objects`
  handles it. Measure a new model with `scripts/a2a_stream.py`; a warm run takes about 15 s, about
  1 s of it tools (`references/a2a-stream.md`).
- **Milvus Lite leaks a gRPC server per database path** until exit. `tests/conftest.py` releases each
  test's servers; without that, subprocess tests crash in gRPC's fork handler once there are
  hundreds of them.
- `claude mcp add --transport http lonekrav http://localhost:8000/mcp` (local scope) is registered
  on this machine; `claude -p ... --output-format stream-json` captures a tool transcript.
