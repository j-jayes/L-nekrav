# Market pulse: evidence (Feature 005)

Run 2026-10-23 on the reference machine (M2 Pro), against `lonekrav-serve` on port 8010 and
the container on 8001. The live numbers change through the day.

## Live open ads match JobSearch (SC-001) and the time per answer (SC-002)

The first 2511 request fetches live; the second reuses the count, with the same `fetched_at`.
Ten codes were sampled with `random.Random(5)` from those with a JobTech concept, and each
was compared with a direct JobSearch call made in the same minute.

```text
2511 200 live=available ads=325 positions=378 fetched_at=2026-10-23T11:29:48.085469Z 353 ms
2511 200 live=available ads=325 positions=378 fetched_at=2026-10-23T11:29:48.085469Z 6 ms

code concept   lonekrav  jobsearch  equal
1251 Pz9M_srJ_Lc9      249        249  True
2352 jJF3_qaQ_Zsh       66         66  True
3151 Rsoy_sS6_6c4        4          4  True
5144 HATH_AfN_RRz       15         15  True
7115 DPPw_4wa_AsH        4          4  True
7213 bXfo_4hb_SXx       32         32  True
7521 v7W3_cLQ_q2S        6          6  True
8159 skLS_kpa_Ui1        9          9  True
8161 gJtZ_EBc_n2z        6          6  True
8344 MrcX_RDn_N53      244        244  True
```

## JobSearch unreachable (SC-003)

The server was started with `LONEKRAV_JOBSEARCH_URL=http://127.0.0.1:9` (a closed port), and
`LiveCache` was pointed at an address that never answers (`10.255.255.1`):

```text
2512 200 0.002339s   (closed port: live.status unavailable, reason 'connection error')
2511 200 0.002058s
salary 200 0.004617s (other routes unaffected)
unavailable timeout 2.00 s  (an address that never answers: one 2 s timeout)
```

In the container with its network disconnected, the market answer was `unavailable connection
error 0.1 s` (`references/container-smoke.md`).

## Positions need their own request (research R1)

With `stats=region`, JobSearch reports `positions: 0`. Without stats it reports the real
figure: for 2512, 1 185 ads and 1 571 positions; with stats, 1 185 ads, 0 positions, and
counties summing to 1 166. So each live count makes two requests.

## Yearly history

`lonekrav-etl fetch --only jobsearch_history` covered 400 concepts × 10 years (2016–2025),
4 000 cached requests, in 69 s on 4 threads. The build wrote 4 000 rows to
`ad_history.parquet`.

The year filter counts by publication date. For 2512 in 2025, the twelve monthly counts add
up to the yearly count, and `published-after`/`published-before` give the same total:

```text
[1935, 1715, 1667, 2547, 2800, 2442, 2068, 1918, 3520, 3696, 3103, 2893] 30304 30304
published-after/before: 30304
```

Summed over the 400 concepts (each shared concept counted once), the yearly totals are:

```text
2016 683735
2017 713592
2018 681694
2019 639535
2020 493026
2021 729194
2022 1060792
2023 1027518
2024 718022
2025 950016
```

For comparison, the historical API reported 686 950 ads in 2016 across all occupations, so
99.5 % of that year's ads carry an occupation-group code.

## Regional means

`TAB5696` was fetched in one request: 11 610 rows (9 areas × 430 codes × 3 years). For every
code and year in both tables, the Sweden row equals TAB5932's mean
(`tests/integration/test_regional_data.py`). TAB4185, which the development plan named, holds
pay within the regions as employers, not pay by area.
