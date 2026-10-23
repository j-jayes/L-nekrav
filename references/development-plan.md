# Lönekrav — development plan

## Context

Non-EU job seekers need a Swedish work permit, and since 1 June 2026 the offer must pay at least 90 % of
the SCB median wage **and** be in line with collective agreements for the SSYK 2012 occupation the employer
writes on the offer. Which 4-digit code the job sits under therefore decides the salary a graduate must
negotiate. Lönekrav is a tool that (1) explains the law, (2) maps a free-text or pasted job description to
the closest SSYK codes in any language, (3) shows the SCB salary distribution for each code against the
statutory floor, and (4) exposes all of that as REST, MCP and A2A so a chat model can use it. Framing is
**honest fit**: show every plausible code and its consequences, state that the code must match the real
duties, never "game the code".

Decisions taken with the user (2026-10-20): A2A v1.0 instead of the archived IBM ACP; second embedder is
`microsoft/harrier-oss-v1-0.6b`; two-speed live search; full spec-kit process; OpenRouter key is in
`.env` (variable is `OPENROUTER_KEY`); monorepo in this repo (remote `j-jayes/L-nekrav`); milestone is the
full stack including React; English enrichment should come from official crosswalks before any LLM.

### Facts verified during research (these override the Gemini planning doc)

| Topic | Verified fact | Source |
|---|---|---|
| Current floor | **34 470 SEK/month** = 90 % of median **38 300** (from 16 June 2026). 75 % level = 28 725. | migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand |
| History | Medians: 32 400 (Jun 2021), 33 200 (Jun 2022), 34 200 (Jun 2023), 35 600 (Jun 2024), 37 100 (Jun 2025), 38 300 (Jun 2026). Rule: 13 000 flat → 80 % from 1 Nov 2023 → 90 % from 1 Jun 2026. | same page + news 2026-06-01 |
| Legal basis | SFS 2026:605 (utlänningsförordningen 5 kap 5–6 b §§, 7 a §): 27 exempt codes at 75 % (3115, 3215, 3511–3514, 5321–5326, 5330, 6121, 6129, 6130, 6210, 7212, 7215, 7233, 7413, 7611, 8161, 8169, 8199, 8341, 9210); permits banned for 5343 and forest berry pickers in 9210; startup (<5 yrs, <100 staff) and former-student/licensing/temporary-protection exemptions at 75 %; union statement (yttrande) step retained; "latest published SCB median on the day the application arrives" governs. | SFS 2026:605 PDF (text extracted) |
| Transition | Extensions filed 1 Jun–1 Dec 2026 for permits granted before 1 Jun keep the 80 % rule; from 2 Dec 2026 everyone is on 90 %. | Migrationsverket news |
| Salary data | SCB PxWeb v2 **TAB5932**: P10/P25/median/P75/P90/mean (+95 % CI) × sector × 4-digit SSYK × sex, 2023–2025 (2025 published 2026-06-16). **TAB5844**: mean + headcount × age band (18–24 … 65–68) × code. TAB5841 same by education level (optional). Suppressed cells arrive as `null`. GET works; `Kon=1+2`, `Sektor=0`. | probed |
| Code list | SCB structure file has **426** 4-digit codes; TAB5932 has 429 real codes (+0000/0001/0002); ISCO key has 429. ETL must reconcile and record the difference in the data dictionary. JobTech has only **400** because it collapses manager "nivå 1/2" pairs (1211/1212 → 1210 etc.) and lacks 4430, 5322, 5324, 7619. | probed |
| English text | SCB publishes official **English titles** for all 426 codes (`structur_english_ssyk2012_1_4.xlsx`), a **9 171-title Swedish index** (`ssyk_index_webb_2026.xlsx`), and an **SSYK→ISCO-08 key** (429 codes; some 1→many, e.g. 2512 → 2511,2512,2513,2514,2521). ILO ships English ISCO-08 definitions with task lists (`ISCO-08 EN Structure and definitions.xlsx`, 303 KB). ESCO API (no auth) gives per-occupation English **and Swedish** titles, alt labels and descriptions, linked to ISCO unit groups; JobTech links every occupation-name to ESCO. So English enrichment is deterministic; the LLM is optional polish. | probed |
| Stack versions | milvus-lite 3.2.2 (pure Python, BM25 Function, sparse, multi-vector, hybrid RRF, FLAT only, Py ≥3.10), pymilvus 3.0.2, a2a-sdk 1.2.3 (`[fastapi]` extra, JSON-RPC + SSE, card at `/.well-known/agent-card.json`), fastmcp 4.1.2 (4.1.3 pinned in 003), mcp 2.3.0, sentence-transformers 6.1.0, spec-kit v1.2.2 (`specify` already installed; commands are `/speckit-constitution`, `-specify`, `-clarify`, `-plan`, `-checklist`, `-tasks`, `-analyze`, `-implement`, `-converge`). | PyPI / probe |
| Machine | Apple M2 Pro, 16 GB, uv 0.9.9, Docker 24, node 22, system Python 3.9 (uv will pin 3.12). KBLab model already in HF cache. | local |
| Latency | Measured 2026-10-20 (`references/embedding-benchmark.md`): KBLab 39 ms per query, 0.73 GB; Harrier fp32 130 ms per query, 0.58 s per pasted ad, 3.1 GB (bf16 is 10× slower on CPU). Container budget raised to **4 GB** by the maintainer, then to **5 GB** in 004 after measuring both models in one container. | measured |

## Repository layout (monorepo)

```
L-nekrav/
├── CLAUDE.md                      # keep; add a short "Lönekrav" project section
├── .claude/skills/                # dev skills copied from j-jayes/slides + speckit-* from specify init
├── .specify/  specs/NNN-*/        # spec-kit
├── .gitignore                     # .env, data/raw/, data/*.db, models/, frontend/node_modules, reports/
├── pyproject.toml  uv.lock        # package "lonekrav", Python 3.12, scripts: lonekrav-etl, lonekrav-serve
├── src/lonekrav/
│   ├── core/                      # framework-agnostic domain: taxonomy, salary, legal, embeddings, search, fluff, eligibility
│   ├── etl/                       # scb_pxweb, scb_files, jobtech, esco, isco, enrich (LLM, optional), index, benchmark, cli
│   ├── api/                       # FastAPI routers under /api/v1
│   ├── protocols/                 # mcp_server.py (FastMCP), a2a_server.py + agent/ (OpenRouter tool loop)
│   └── app.py                     # one FastAPI app mounting /api/v1, /mcp, /a2a, static frontend
├── data/raw/ (gitignored)  data/processed/ (small JSON/parquet artefacts, committed, with data-dict.yaml)
├── tests/                         # pytest; tests/eval/ holds the cross-lingual benchmark
├── frontend/                      # Vite + React 19 + TS + Tailwind
├── docker/Dockerfile  docker-compose.yml
├── references/                    # working examples hoarded per CLAUDE.md §7
└── docs/walkthroughs/
```

## Step 0 — bootstrap (before any spec-kit command)

1. `.gitignore` first (the `.env` with the OpenRouter key is untracked and must never be committed).
2. Copy development skills from `github.com/j-jayes/slides/skills` into `.claude/skills/`: `tdd`,
   `manual-testing`, `first-run-the-tests`, `git-discipline`, `subagent-fanout`, `walkthrough`, `data-dict`
   (with its `reference/`), plus `viz-index`, `viz-distributions`, `viz-colour`, `viz-labels`, `viz-review`
   for the charts. Clone the repo to the scratchpad and `cp -r`, do not retype.
3. `specify init --here --force --integration claude` (adds `.specify/`, `.claude/skills/speckit-*`).
4. `uv init --package`, pin Python 3.12, add `ruff`, `pytest`, `pydantic>=2`, `httpx`.
5. Append a "Lönekrav" section to `CLAUDE.md`: layout above, `uv run pytest` as the suite command,
   `OPENROUTER_KEY` name, "never fabricate SCB numbers" rule. Leave the existing Slides section alone.
6. First commit on `main`; everything after goes through feature branches + PRs (spec-kit's
   `create-new-feature.sh` makes `NNN-name` branches).

Verify: `git status` clean, `.env` ignored, `uv run pytest` reports "no tests ran" (not an error),
`/speckit-constitution` is listed by the Skill tool.

## Spec-kit cycle 0 — constitution (`/speckit-constitution`)

Principles to encode (ready to paste, then edit):

1. **Core first, adapters thin.** All logic in `src/lonekrav/core/`; `/api/v1`, `/mcp`, `/a2a` are adapters
   that only validate, call core, and serialise. A core function must be callable from a pytest with no
   server running.
2. **Data integrity.** Never fabricate or silently interpolate SCB figures. Every salary payload carries
   `source_table`, `reference_year`, `fetched_at`; nulls stay null; derived numbers carry
   `is_simulated: true` and the formula. Legal constants live in one registry with effective dates and
   a source URL per row.
3. **Honest fit.** Code comparison shows consequences and official task text; copy never advises
   choosing a code that does not match the duties. Every legal statement links its source and shows a
   "checked on" date.
4. **TDD and manual proof.** Red before green; nothing is "done" until run for real (curl, CLI, screenshot)
   and the evidence is in the PR. Bugs found by hand become tests.
5. **Compact and portable.** `docker compose up --build` runs the whole stack; memory budget measured and
   recorded; Milvus Lite file by default, `MILVUS_URI` switches to a server.
6. **Simplicity and surgical change** (import CLAUDE.md §1–3 verbatim).
7. **Tooling.** Python 3.12 + uv + ruff + pydantic v2 + pytest; React 19 + TS + Vite + Tailwind; English UI
   with Swedish terms alongside.

## Feature 001 — `001-data-taxonomy-index`

**Spec (what):** one canonical record per 4-digit SSYK code with Swedish + English titles, official
descriptions, synonyms in both languages, ISCO/ESCO links, legal flags (exempt-75 %, banned), salary
percentiles 2023–2025, age-band means, and a Milvus Lite index that answers bilingual queries. A benchmark
proves English and Swedish queries retrieve the same codes.

**Plan (how):**

- `etl/scb_files.py`: download + parse the four SCB xlsx files (codes, English structure, title index,
  ISCO key). `etl/scb_pxweb.py`: TAB5932 (Sektor=0, Kon=1+2, all years, six measures) and TAB5844
  (all age bands, Månadslön + Antal anställda) via GET, json-stat2, cached raw to `data/raw/`.
- `etl/jobtech.py`: GraphQL `ssyk-level-4` (definition, narrower occupation-name with alternative_labels),
  and occupation-name → esco-occupation matches. Map JobTech 3-digit-style manager codes onto both SCB
  nivå codes.
- `etl/isco.py`: ILO xlsx → English definition + task list per ISCO unit group. `etl/esco.py`: for each
  ISCO group in the SCB key, fetch `narrowerOccupation` and each occupation in `en` and `sv` (title, alt
  labels, description); cache per URI. Attribution to the European Commission in the data dictionary;
  confirm licence text during the task.
- `etl/enrich.py` (optional, skippable): OpenRouter batch adding 10–15 English corporate titles per code,
  cached to `data/processed/llm_synonyms.json`, flagged `source: llm`.
- `core/taxonomy.py` builds the `SsykProfile` pydantic model and writes
  `data/processed/ssyk_2012_profiles.json` + `salary_stats.parquet` + `data-dict.yaml` (use the
  `data-dict` skill; interview the user for anything guessed).
- `core/embeddings.py`: registry with `kblab` (768d, `KBLab/sentence-bert-swedish-cased`) and `harrier`
  (1024d, `microsoft/harrier-oss-v1-0.6b`, query prompt `Instruct: …\nQuery: …`, documents bare). Measure
  CPU latency and RSS for both; try int8/ONNX for Harrier if fp32 breaks the memory budget. Record the
  numbers in `references/embedding-benchmark.md`.
- `core/milvus_store.py`: collection `ssyk_profiles` (one doc per code: `vec_kblab`, `vec_harrier`,
  BM25 sparse over bilingual text, scalar fields) and `ssyk_titles` (one doc per synonym/title,
  ~15 k rows, aggregated to codes by max score). Hybrid search with `RRFRanker`. Decide after the
  benchmark whether the title collection earns its keep.
- `tests/eval/cross_lingual.py`: ≥40 EN/SV query pairs (titles → multi-sentence duties, incl. tricky
  ones: data analyst vs statistician vs organisationsutvecklare; nurse variants; manager nivå 1/2).
  Metrics Recall@1/@5, MRR per model and fused; output table + `data/processed/benchmark_results.json`.
- CLI: `uv run lonekrav-etl fetch | build | index | benchmark`, idempotent, re-runnable.

**Verify:** pytest for parsers on fixture slices; `lonekrav-etl build` yields 429 (or 426, documented)
profiles with zero missing English titles; `index` → Milvus file < 200 MB; benchmark shows EN and SV
Recall@5 within a few points of each other and the fused run ≥ either model; spot-check "backend
developer", "sjuksköterska", "management consultant" by hand from a `python -c` one-liner.

## Feature 002 — `002-search-eligibility-api`

**Spec:** (a) job-ad signal extraction: paste → segments labelled role_duty / skill / company_fluff /
benefits with keep flag; (b) live search returning top-k codes with per-model scores, fused rank and
matched text, fast path (kblab + BM25) and full path (adds Harrier); (c) eligibility: salary, FTE %,
application type and date, prior-permit date, exemption flags, selected code → which threshold applies,
pass/fail, margin, and the part-time warning (floor is not prorated); (d) distribution payload per code:
percentiles, age means, simulated age-adjusted quantiles (`p_age = p × mean_age / mean_all`, flagged),
P10–P25 band, floor lines; (e) compare 2–5 codes side by side with official task text.

**Plan:** `core/fluff_stripper.py` (sentence split + anchor-vector classifier with kblab, <15 ms),
`core/legal.py` (`LegalConstants` registry: every row above with effective dates + source URLs),
`core/eligibility.py`, `core/salary.py`, `core/search.py`. FastAPI routers: `POST /api/v1/parse-job-ad`,
`POST /api/v1/search` (`mode: fast|full`), `POST /api/v1/eligibility`, `GET /api/v1/occupations/{code}`,
`POST /api/v1/compare`, `GET /api/v1/legal/timeline`, `GET /api/v1/benchmark`. Pydantic response models
are the single contract shared with MCP/A2A/React.

**Verify:** TDD on legal/eligibility edge cases (application dated 15 Jun 2026 vs 16 Jun; extension filed
30 Nov vs 2 Dec 2026; 80 % FTE at 40 000 SEK; code 5343 → banned; 3511 → 75 %); fast search p95 < 50 ms
and full < 1 s measured with a small `hey`/httpx loop; `curl` transcript saved to `references/api-smoke.md`.

## Feature 003 — `003-mcp-a2a-protocols`

**Spec:** any MCP client can call `search_occupations`, `extract_job_ad_signal`,
`get_occupation_salary`, `evaluate_permit_eligibility`, `compare_occupations`, and read resources
`legal://timeline`, `ssyk://{code}`. An A2A agent `lonekrav-advisor` is discoverable at
`/.well-known/agent-card.json`, accepts a job ad + background + offer, streams status updates, tool-call
artefacts (so a UI can sync its charts) and a final memo in the honest-fit voice.

**Plan:** `protocols/mcp_server.py` with FastMCP 4, mounted via `mcp.http_app()` at `/mcp`;
`protocols/a2a_server.py` with `create_agent_card_routes` + `create_jsonrpc_routes` (`DefaultRequestHandler`,
`InMemoryTaskStore`), `AgentExecutor` running an OpenAI-compatible tool loop against
`https://openrouter.ai/api/v1` (`OPENROUTER_KEY`, `LONEKRAV_LLM_MODEL` env, default a cheap fast model),
binding the same core functions as MCP; `ui_sync` payloads as structured artifact parts. Unit tests run
the executor against a fake model client; one live smoke test skipped without the key.

**Verify:** `claude mcp add --transport http lonekrav http://localhost:8000/mcp` and call a tool from
Claude Code; A2A: fetch the card, then a `message/stream` call with the a2a-sdk client printing events;
save both transcripts to `references/`.

**As built (2026-10-22)**: the decisions are in `specs/003-mcp-a2a-protocols/research.md`.
- fastmcp 4.1.3 is mounted at `/` with `http_app(path="/mcp")`, so the endpoint is exactly `/mcp`.
- The REST adapter's rules moved to `core/service.py`, which all three surfaces call.
- The advisor's tools are the MCP server's own, used through an in-memory `fastmcp.Client`.
- A2A v1.0 names the streaming method `SendStreamingMessage`; `message/stream` is the 0.3 name.
- Without a key, tasks end `rejected`.
- The default model is `anthropic/claude-haiku-5.5`: about 1 s per round, and about 15 s for a
  warm memo run, of which about 1 s is tools.

The transcripts are `references/mcp-claude-code.md` and `references/a2a-stream.md`.

## Feature 004 — `004-web-client-docker`

**Spec:** English single-page app with: legal guide + timeline + part-time calculator; paste/typing
search with signal-vs-fluff highlighting and a per-model score strip (kblab/BM25 instant, Harrier arrives
on pause); distribution chart per selected code (P10–P90 bar, floor line at the applicable threshold,
P10–P25 band, age-band mean dots, toggleable simulated age-adjusted ghost bar, up to 4 codes); compare
view with official task text; A2A chat drawer that can select codes on the chart. `docker compose up
--build` serves everything on one port.

**Plan:** Vite + React 19 + TS + Tailwind; chart as hand-written SVG following the `dataviz` skill
(load it before the first chart) and `viz-distributions`; `frontend/src/lib/a2aClient.ts` (JSON-RPC over
fetch + SSE parsing); typed client generated from the FastAPI OpenAPI schema. Multi-stage Dockerfile:
node build → python 3.12-slim with `uv sync --frozen`, models pre-downloaded into the image (or a cache
volume), FastAPI serves `frontend/dist`; compose sets `mem_limit` to the measured budget. Document the
Cloud Run variant in the README without deploying it.

**Verify:** Playwright screenshots of the three main views at phone and desktop width; `docker stats`
RSS recorded; end-to-end: paste a real LinkedIn ad in English, then its Swedish translation, confirm the
same top-3 codes; A2A drawer updates the chart.

**As built (2026-10-22)**: the decisions are in `specs/004-web-client-docker/research.md`.
- The page is served at `/` and `/assets`, before the MCP root mount. Its state lives in the query
  string, so no catch-all route is needed.
- The page's types are generated from the committed OpenAPI schema, which a drift test guards.
- The chart is hand-written SVG, and every figure comes from the payloads, including
  `applicable_rule_id` for the floor.
- The A2A client is fetch plus an SSE parser, tested on captured bytes.
- The image bakes in both models and the index. It uses CPU-only torch on Linux and a uv cache
  mount, and is 3.85 GB.
- The cap is 5 GB, because the measured peak is 4.54 GiB.

Found and fixed along the way:
- ILO text was served as the matched passage. ILO chunks now rank but are never shown.
- 002's ad parser let one heading label an entire ad.

The English/Swedish top-three check failed on two real Platsbanken ads, the cross-lingual ranking
of whole ads (`references/web-client-e2e.md`). Evidence: `references/web-client-e2e.md`,
`references/container-smoke.md`, `references/container-memory.md` and
`references/web-client-screenshots/`.

## Extension (not in milestone) — `005-market-pulse`

JobSearch API live counts and regions per code (probe: `occupation-group=DJh5_yyF_hEM` returns 1 172
open ads), pre-aggregated historical counts later. Regional salary tables (TAB4185) could join here.

**As built (2026-10-23)**: the decisions are in `specs/005-market-pulse/research.md`.
- **Live demand**: two JobSearch requests per count, because `positions` is 0 whenever stats are
  requested. Each has a 2 s timeout, and counts are reused for 15 minutes. A failure is
  "unavailable", with no number.
- **Regional pay**: from **TAB5696**, not TAB4185. TAB4185 holds the pay of people employed by
  the regions (county health-care employers), not pay by area. TAB5696 gives means only, for 8
  national areas.
- **Yearly ads**: 2016–2025 from the historical ads API (4 000 cached requests, 69 s).
- **Surfaces**: `GET /api/v1/occupations/{code}/market`, the MCP tool `get_occupation_market`
  (which the advisor may cite), and a market panel under each compare column.

Evidence: `references/market-pulse.md`.

## Process per feature

`/speckit-specify` → `/speckit-clarify` → `/speckit-plan` → `/speckit-checklist` → `/speckit-tasks` →
`/speckit-analyze` → `/speckit-implement` → `/speckit-converge`, on branch `NNN-name`, one PR per
feature (smaller PRs inside it where natural), each PR carrying run output or screenshots. Start each
session with `first-run-the-tests`. End each feature with a `walkthrough` in `docs/walkthroughs/` and a
compound step that folds anything learned into `references/` or `CLAUDE.md`.

## Open risks to watch

- Harrier memory/latency on CPU; fallback is `google/embeddinggemma-300m` behind the same registry.
- Which 3 codes differ between the 426-code structure file and the 429-code salary table.
- ESCO licence wording (attribution expected; confirm before shipping the data file).
- The SCB median changes every June; the legal registry needs a yearly update task and a stale-data banner.
