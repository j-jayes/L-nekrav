# Research: Feature 002

Measured on the maintainer's laptop (M2 Pro, 16 GB) on 2026-10-21 against the local Feature 001
index (9 556 chunks) and `data/processed/benchmark_results.json` from the same day. Legal facts
fetched the same day from Migrationsverket.

## R1. Why Swedish scores 10 points lower than English (FR-018, Story 3)

The gap has two causes. Neither is the dense models.

**Cause 1: the English generated queries leak into the index.** The English side of a generated
pair is an ESCO preferred label. The hold-out check (`etl.benchmark._Leaks`) only blocks exact
phrase matches, and ESCO descriptions, which are indexed, almost always open with the label in the
plural ("business managers are responsible for…"). Allowing up to three trailing word characters:

| Paired generated queries | n | Label found in indexed text of the answer |
|---|---|---|
| English | 111 | **104** |
| Swedish (any slash part) | 111 | 23 |

So the English generated set is close to a lookup. Harrier English generated Recall@1 is 0.991.

**Cause 2: Swedish BM25 drags the fusion down.** On the 32 hand-written pairs, which do not leak:

| Recall@5 | EN | SV |
|---|---|---|
| kblab | 0.969 | 0.969 |
| harrier | 0.969 | 0.969 |
| bm25 | 0.875 | **0.625** |
| fused (equal-weight RRF) | 0.969 | **0.906** |

Both dense models are already equal across languages. Fused Swedish is *worse* than either dense
model alone, which also breaks SC-006's spirit. `references/benchmark-fusion-diagnostic.txt`
(diagnostic run, 2026-10-21) shows the same: dropping BM25 lifts hand-written top-5 overlap from
0.625 to 0.812.

**Slash-joined queries** are 40 of 353 generated queries but only 8 of the 111 paired ones, so they
explain little of the paired gap; FR-013a still handles them in search (R4).

**Decision**
1. Make the leak check inflection-aware (a phrase followed by up to three word characters counts as
   present) and apply it to both languages. A generated pair whose English label leaks tries the
   next ESCO exact/close label; if none is clean it becomes Swedish-only. Report the new paired n.
2. Keep the 001 results as `data/processed/benchmark_results_001.json` and print old and new side by
   side (FR-019).
3. Fix the fusion for Swedish, in this order, stopping at the first that passes the gates: (a)
   per-method RRF weights, with BM25 weight chosen on the generated set and confirmed on the
   hand-written set; (b) analyser improvements in `core/text.py` if (a) is not enough. Tuning on the
   generated set and confirming on the hand-written set keeps the 32 pairs from being overfitted.
4. Hand-written overlap (0.69) is re-measured after 3; the diagnostic run suggests BM25 is the cause.

**Risk**: after step 1 the paired generated set may shrink sharply, so the gap rests on fewer
queries (one query ≈ 2.5 points at n = 40). The benchmark output prints n beside every metric; if
paired n falls below 60, raise it with the maintainer before trusting the gate.

**Alternatives rejected**: retuning or replacing the dense models (they are already equal across
languages); dropping BM25 from the fused ranking (it is the best English method on titles and the
fast path needs it); editing slash-joined queries (ruled out in clarification).

## R2. Fast path in 50 ms (SC-003)

Measured, 6 queries × 5–10 repeats, models warm:

| Step | Median | p95 |
|---|---|---|
| Current fast `search()` (kblab + bm25) | 76.8 ms | 99.2 ms |
| KBLab encode, 4 threads (default) | 36.2 | 42.1 |
| KBLab encode, 1 thread | 30.8 | 36.7 |
| Milvus Lite dense FLAT search, pool 200 | 25.7 | 29.3 |
| numpy matmul over 9 556 × 768 + argpartition | 0.4 | 0.5 |
| BM25, pool 200 / pool 50 | 14.5 / 6.4 | 16.1 / 8.0 |
| **Encode (1 thread) + numpy dense + BM25 pool 50, sequential** | **37.2** | **42.7** |
| Encode in parallel with BM25 (2 threads) | 53.8 | 65.0 |

**Decision**: (1) load each model's dense vectors from the store once at startup into a normalised
numpy matrix and search it with a matrix product; the store stays the source of truth, so a Milvus
server (`MILVUS_URI`) works the same; (2) encode queries with one torch thread; (3) fetch 50 chunks
per method instead of 200 for the fast path, after confirming on the benchmark that recall does not
drop; (4) no threading. Memory: 9 556 × (768 + 1 024) × 4 bytes ≈ 68 MB.

**Alternatives rejected**: ONNX or int8 KBLab (more moving parts; not needed to meet the budget);
parallel encode and BM25 (slower on this machine because of thread contention).

## R3. Full path in 1 second (SC-003)

From `references/embedding-benchmark.md`: Harrier fp32 is 130 ms per query and 0.58 s per pasted ad.
With R2's fast path (≈ 45 ms) and parsing (R5), a pasted ad stays under 1 s if Harrier encodes the
kept text once. **Decision**: the full path runs kblab, Harrier and BM25 sequentially. Harrier loads
lazily on the first full request; if it fails to load, the request falls back to fast mode and the
answer says so (FR-014). The quickstart measures p95 on a 600-word ad.

## R4. Slash-joined titles (FR-013a)

**Decision**: text is a title list when it contains "/", has no sentence punctuation (. ! ? or a
line break), and every part has at most six words. Each part is encoded in one batch call; for each
method the chunk hits from all parts are pooled and reduced with the existing `reduce_to_codes` (best
chunk per occupation), then fused as usual. "Game designer/Speldesigner" becomes two searches;
"and/or" inside a sentence is untouched. The benchmark calls the same function (FR-017).

## R5. Job-ad parsing (FR-021–FR-023)

**Decision**: a deterministic splitter plus a small classifier, no LLM:
1. Split on lines and bullets, then on sentences inside long lines.
2. A heading lexicon (sv and en: "Om oss", "About us", "Arbetsuppgifter", "Responsibilities",
   "Kvalifikationer", "Requirements", "Vi erbjuder", "What we offer", …) labels the passages that
   follow it until the next heading.
3. Passages outside any headed section are labelled by nearest centroid of KBLab embeddings over a
   small committed set of anchor sentences per label and language.
4. The first short line (≤ 10 words, no final full stop) before any heading is the title.

Passages are encoded in one batch; a 600-word ad is about 40 passages. Accuracy is checked on ten
real ads (five per language). **Source**: JobTech's public JobSearch API; the ad licence is still
unconfirmed (open item from 001), so the ads are cut into `tests/fixtures/ads/` by
`scripts/cut_fixtures.py` only after the licence is confirmed. Until then the test uses made-up ads
written to resemble real ones, and SC-005 stays open.

**Alternatives rejected**: an LLM classifier (needs the key, FR-022); a trained classifier (no
labelled corpus; anchors plus headings are enough to try first).

## R6. Legal registry and the rules (FR-001–FR-012)

Sources, fetched 2026-10-21:
- https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand
- https://www.migrationsverket.se/ordforklaringar/god-forsorjning---forsorjningskrav-for-arbetstillstand.html
- SFS 2026:605 (already cited by `core/legal_flags.py`)

Facts that corrected the spec:
- The new salary requirement applies to **first permits decided** from 1 June 2026, including
  applications filed earlier. The median is the one in force on the **filing** date.
- The exempt-code list in force on the **decision** date applies; an extension must check the code
  is still listed.
- Extensions filed 1 June–1 December 2026 on permits granted before 1 June 2026 must meet the
  earlier maintenance requirement (god försörjning, 80 %), which has no 75 % exemption. From
  2 December 2026 the new requirement applies to them. Extensions of permits granted from 1 June
  2026 follow the new requirement.
- The four personal exemption groups are: former students and researchers applying for a first
  work permit; people with temporary protection under the EU mass-displacement directive (two years
  or the permit's length); doctors, dentists and nurses with a foreign degree becoming licensed;
  employees of tech or life-science companies under five years old with fewer than 100 staff.
- EU Blue Card, ICT, seasonal workers and several other permit types are exempt from the
  maintenance requirement; they are out of scope.

Median table (Migrationsverket):

| Took effect | Median | 90 % | 75 % | 80 % |
|---|---|---|---|---|
| 2026-06-16 | 38 300 | 34 470 | 28 725 | 30 640 |
| 2025-06-17 | 37 100 | 33 390 | 27 825 | 29 680 |
| 2024-06-18 | 35 600 | 32 040 | 26 700 | 28 480 |
| 2023-06-20 | 34 200 | 30 780 | 25 650 | 27 360 |
| 2022-06-21 | 33 200 | 29 880 | 24 900 | 26 560 |
| 2021-06-22 | 32 400 | 29 160 | 24 300 | 25 920 |

Every published amount is an exact product, so amounts are computed with `Decimal` and rounded half
up to whole kronor; a test checks every row against the table.

**Decision**: the registry is a committed YAML file, `src/lonekrav/core/legal_constants.yaml`,
loaded and validated by pydantic models in `core/legal.py`. Each row carries `effective_from`,
`effective_to`, `source_url` and `checked_on`. The yearly June update edits only this file, and a
test fails if the file has no median for the current year after 22 June (the latest date a median
has taken effect), so the stale registry is noticed in CI as well as in answers (FR-005).
`core/legal_flags.py` keeps its `flags_for` signature but reads the code sets from the registry.

**Alternatives rejected**: Python constants (as in 001): every yearly update becomes a code change
and the source and checked-on fields are easy to drop.

## R7. Web API (FR-029–FR-033)

**Decision**: FastAPI with uvicorn; one router module `api/v1.py`; `app.py` builds the app (003 will
mount `/mcp` and `/a2a` on it); `lonekrav-serve` entry point. Request and response models are core
pydantic models (FR-030); FastAPI publishes the OpenAPI document at `/api/v1/openapi.json`. The
store, the KBLab model and the dense matrix load once in the app lifespan. Input limits: query and
ad text 20 000 characters; k ≤ 20. Errors are FastAPI 422s naming the field; a handler turns any
other exception into a 500 with no path or traceback (FR-031).

Request contents are **not logged** at all: FR-033 allows debug logging but does not require it,
and not logging is simpler and safer. Logs hold method, path, status and duration only.

## R8. Low-confidence note (FR-016)

**Decision**: the cut-off is the top fused hit's best dense cosine (KBLab, which both modes run).
It is chosen from the benchmark: the highest value that keeps at least 95 % of benchmark queries
above it, checked against a short list of nonsense queries in `tests/eval/nonsense.yaml` (for
example "asdf", "qwerty uiop"). The value and how it was derived are written into the benchmark
results and read by search.

## R9. Dependencies

Add `fastapi` and `uvicorn` (runtime). The tests use FastAPI's `TestClient` with an in-memory store
built on the FakeEmbedder, as 001's integration tests do. No other new dependencies.
