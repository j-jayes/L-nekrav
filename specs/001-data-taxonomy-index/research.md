# Research: SSYK Occupation Dataset and Bilingual Search Index

All findings below were checked against the live sources on 2026-10-20. Probe commands are in the
session log; the Milvus spike is saved as `references/milvus_lite_hybrid.py`.

## R1. Canonical code list

- **Decision**: The canonical set is the 429 occupation codes in SCB salary table TAB5932 (excluding
  0000, 0001, 0002). That is the 426 codes in the SCB structure workbook plus the three military codes
  0110, 0210 and 0310, which the workbook omits but the salary table and ISCO key include.
- **Rationale**: Salary data is the product's purpose, and every structure code is in the salary
  table. No code is in the structure file only.
- **Coverage found**: structure workbook 426; ISCO key 429; title index 430 codes (includes 3-digit
  rows padded to 4, which are filtered); JobTech 400. JobTech lacks 4430, 5322, 5324, 7619 and all
  50 manager "nivå 1/2" codes, which it merges into level-0 codes (for example 1210 for 1211 and
  1212). JobTech also returns 28 level-0 codes that SCB does not use in its salary tables.
- **Alternatives considered**: the structure workbook as master (drops the military codes);
  JobTech as master (drops 54 codes).

## R2. Swedish descriptions

- **Decision**: Primary source is the JobTech `ssyk-level-4` definition (SCB's own text, with "Hit hör
  inte" exclusions). For the 54 codes JobTech lacks or merges, parse the description section of the
  SCB publication *SSYK 2012* (MIS 2012:1, PDF, 178 pages). Merged manager codes take the level text
  from the publication plus the shared group text, labelled as shared.
- **Rationale**: Both texts are official SCB wording. The workbook has no descriptions (checked: no
  filled columns beyond code and title).
- **Risk**: The PDF has an overview list and correspondence tables that also contain codes, so the
  parser must target the description section only. Tested against three fixture codes (1212, 4430,
  5322).
- **Alternatives considered**: JobTech only (leaves 4 codes without a description); LLM-written
  descriptions (violates Principle II).

## R3. English titles and descriptions

- **Decision**: English title from SCB `structur_english_ssyk2012_1_4.xlsx` (426 codes), with ILO
  ISCO-08 titles for the three military codes. English definitions, task lists and example
  occupations from the ILO `ISCO-08 EN Structure and definitions.xlsx` (436 unit groups, columns:
  Definition, Tasks include, Included occupations, Excluded occupations), joined through the SCB
  SSYK→ISCO key. Each ISCO group is kept separately, labelled with its code.
- **Rationale**: Deterministic, official, and complete. The ILO "Included occupations" lists give
  English job titles for free.
- **Alternatives considered**: ESCO ISCO-group descriptions (the same ILO text); LLM translation
  (deferred, see R6).

## R4. Synonyms and ESCO links

- **Decision**: Swedish synonyms from the SCB title index (9 171 titles) and JobTech occupation-names
  with their alternative labels. English and Swedish ESCO labels are attached **only through
  JobTech's occupation-name → esco-occupation matches** (exact, close, broad, narrow; match type
  kept). ESCO occupations are fetched per URI from the ESCO REST API in `en` and `sv` and cached.
- **Rationale**: ISCO groups do not map one-to-one to SSYK (for example SSYK 2512 maps to five ISCO
  groups). Reaching ESCO through ISCO would attach occupations to the wrong SSYK code. JobTech's links
  are made at the job-title level. A sample of 300 occupation-names all had an ESCO match.
- **Licence**: ESCO is published by the European Commission, free of charge. The exact reuse wording
  is to be confirmed and recorded in the data dictionary (open item for implementation).

## R5. Salary tables

| Years | Percentiles and mean | Age bands | Confidence intervals |
|---|---|---|---|
| 2014–2022 | TAB4265 (contents C5–CA) | TAB4264 (Månadslön C4, Antal C1) | not published |
| 2023–2025 | TAB5932 (contents 7CD–7CI, CIs 7CJ–7CO) | TAB5844 (Månadslön 7BN, Antal 7BK, CIs) | published |

- **Decision**: Fetch with GET `…/tables/{id}/data?outputFormat=json-stat2` with `Sektor=0`,
  `Kon=1+2`, all codes and all years. Each year comes from exactly one table, recorded per row.
  Nulls in json-stat2 are suppressed cells and stay null with `suppressed: true`.
- **Rationale**: Verified by fetching 2512 and 0000 for 2025 (median 53 500 and 38 300). POST with a
  JSON selection returned "Non-existent value" errors; GET works.
- **Fixture values**: 0000 in 2025: mean 42 900, median 38 300, P10 28 000, P25 32 000, P75 48 000,
  P90 61 700. 2512 in 2025: mean 55 500, median 53 500, P10 39 600, P25 46 200, P75 62 600,
  P90 72 600. Age means for 2512 in 2025: 18–24 36 100 (headcount suppressed), 25–34 49 300,
  35–44 56 600, 45–54 61 100, 55–64 62 300, 65–68 58 800, all ages 55 500.

## R6. LLM enrichment

- **Decision**: Not built in this feature. FR-008 is optional, and R3 and R4 already give English
  titles from three official sources. Revisit only if the benchmark shows an English gap above SC-005.
- **Rationale**: Principle VI (no features beyond the need) and Principle V (no LLM dependency in
  pipelines).

## R7. Vector store and fusion

- **Decision**: One Milvus Lite collection, `occupation_chunks`, with one row per text chunk of an
  occupation (title block, Swedish description, each English ISCO definition, synonym blocks). Fields:
  `chunk_id`, `code`, `kind`, `lang`, `text` (BM25 analyzer, `standard`), `vec_kblab` (768),
  `vec_harrier` (1024), and the BM25 sparse output field. Each method is searched separately, chunk
  scores are reduced to one score per code by taking the maximum, and the three code rankings are
  fused in core with reciprocal rank fusion (k = 60).
- **Rationale**: KBLab's encoder truncates at a few hundred tokens, so a whole profile in one vector
  would lose most of its text. Chunking keeps all of it. Fusion has to happen after the reduction to
  codes, and Milvus's built-in `RRFRanker` fuses chunk lists, so the fusion step is ten lines in core.
  The spike confirmed that Lite 3.2 supports two dense fields, a BM25 function field and hybrid search
  in one collection (5 ms on 4 rows).
- **Gotcha**: Milvus Lite returns BM25 distances as negative numbers. Core converts them so that a
  higher score is better for every method.
- **Alternatives considered**: one row per occupation (truncation); Milvus `hybrid_search` with
  `RRFRanker` over chunks (fuses the wrong unit); a separate collection per method (more files, no
  benefit).

## R8. Embedding models

- **Decision**: `KBLab/sentence-bert-swedish-cased` (768d, already in the local HF cache) and
  `microsoft/harrier-oss-v1-0.6b` (1024d, MIT, Swedish listed, MTEB multilingual v2 score 69.0).
  Harrier queries use the model's preconfigured `web_search_query` prompt, and documents are encoded
  without a prompt. Both are L2-normalised and searched by cosine.
- **Measurement task**: The first implementation task measures, on the M2 Pro CPU, the time per short
  query, per 600-word pasted ad and for the full corpus, plus resident memory per model, in fp32 first.
  Results go to `references/embedding-benchmark.md`.
- **Measured (2026-10-20)**: KBLab fp32 0.73 GB peak, 39 ms per short query. Harrier loads as bf16
  by default, which is about 10× slower on CPU (5.9 s per 600-word ad), so it MUST be loaded in fp32:
  130 ms per short query, 0.58 s per ad, 130 ms per document, 3.1 GB peak.
- **Budget decision (maintainer, 2026-10-20)**: the container memory budget is 4 GB, with Harrier in
  fp32. No quantisation. `google/embeddinggemma-300m` remains the documented fallback if a smaller
  target is needed later.

## R9. Testing without models

- **Decision**: Core takes an `Embedder` protocol (`name`, `dim`, `encode_queries`,
  `encode_documents`). The default test suite uses a deterministic hashed bag-of-words fake embedder
  and a Milvus Lite file in a temp directory, so it runs offline in seconds. `pytest -m benchmark`
  loads the real models and asserts SC-004, SC-005 and SC-006.
- **Rationale**: This was a clarification answer and follows Principle IV.

## R10. Benchmark construction

- **Decision**: (a) `tests/eval/queries_handwritten.yaml`: at least 30 English/Swedish pairs with
  types `title`, `duty_sentence`, `description` and `lookalike`, each listing acceptable codes.
  (b) Generated set: a seeded stratified sample of at least 200 JobTech occupation-names, at most one
  per SSYK code, with Swedish text from JobTech and English text from the matched ESCO preferred label
  where one exists. Hold-out titles are written to `data/processed/benchmark_holdout.json` and
  excluded from chunk text, including the alternative labels of the same occupation-name.
- **Metrics**: Recall@1, Recall@5 and MRR per method (kblab, harrier, bm25, fused) × language ×
  origin, plus the EN−SV gap.

## R11. Output formats

- **Decision**: `ssyk_profiles.json` (UTF-8, sorted by code, pretty-printed for reviewable diffs);
  `salary_distributions.parquet`, `salary_age.parquet` and `discrepancies.csv` written with polars;
  `data-dict.yaml` following the tidyverse data-dict spec (data-dict skill). Every salary row carries
  `source_table`, `reference_year` and `fetched_at`, where `fetched_at` is the time the raw file was
  downloaded (stored beside it in `data/raw/`), not the build time. A rebuild from cache is therefore
  byte-identical.
