# Web client end to end (Feature 004)

Recorded on 2026-10-22 against `lonekrav-serve` with the real index (Apple M2 Pro), through the
built page in Chromium (Playwright 1.64). The suites are in `frontend/e2e/`. Screenshots of the three
views at 390 and 1280 px are in `references/web-client-screenshots/`.

## The two real ads (SC-003)

Both ads are public on Platsbanken. Only their links and the resulting codes are committed here.
The Swedish versions are translations made by the model (Claude) during this feature, not human
translations. The run is `e2e/ad-languages.spec.ts` with `AD_EN` and `AD_SV` pointing at the two
files.

| Ad | Platsbanken | English top 3 | Swedish top 3 | Same set? |
|---|---|---|---|---|
| Intensive Care Nurse for the ICU, Torsby Hospital (Region Värmland, 613 words) | [31520533](https://arbetsformedlingen.se/platsbanken/annonser/31520533) | 2228, 2224, 2221 | 5323, 2239, 2221 | **no** |
| Backend Developer (BTR Personnel services AB, 399 words) | [31551762](https://arbetsformedlingen.se/platsbanken/annonser/31551762) | 2512, 2511, 2519 | 2511, 2512, 3155 | **no** (top 2 agree) |

**SC-003 is not met on these two ads.** What was found along the way:

- **Ad parsing (fixed in this feature)**: the Swedish nurse ad's "Om tjänsten" heading made all 42
  passages duties, because the headings after it were not in the list. An unknown heading now ends
  the section (commit "adparse: an unknown heading ends the section before it"). This sets aside 17
  passages, close to the English 21, and the benchmark is unchanged.
- **Ranking (not changed: outside 004)**: in Swedish, the nurse ad's mention of the
  *undersköterska* (assistant nurse) the ICU nurse works with ranks 5323 first in every model, and
  2228 drops to fifth. 002's cross-lingual benchmark measures short queries, not whole ads. These
  two pairs are candidates for an ad-level benchmark.

## Timings (SC-001, SC-002)

| Measure | Nurse ad | Backend ad | Target |
|---|---|---|---|
| Keystroke to the list matching the box ("intensive care nurse", typed): median / max | 50 / 253 ms | 51 / 199 ms | 0.5 s |
| Paste to the accurate ranking on screen, English | 1.8 s | 1.8 s | 3 s |
| Paste to the accurate ranking on screen, Swedish | 2.3 s | 2.3 s | 3 s |

The paste figures include the 600 ms pause before the accurate search starts. Before the parsing
fix, the Swedish nurse ad took 4.3 s, because every passage was searched.

## Advisor drawer (SC-008)

- **Scripted model** (`scripts/serve_fake_advisor.py`, `e2e/advisor.spec.ts`, phone and desktop):
  2512 and then 2511 appear on the chart before the memo arrives, and the address updates to
  `codes=2512%2C2511`. Both widths pass.
- **Live model** (`anthropic/claude-haiku-5.5` via OpenRouter, the backend example ad
  `tests/fixtures/ads/en1_backend.txt` with a short background, no offer): the first progress line
  came at 0.3 s, the first code on the chart at 12.9 s, and the memo at 20.5 s. The progress lines
  were "Reading the job ad", "Calling search_occupations" and "Calling get_occupation_salary"
  (twice). The chart ended with 2512 and 2511. The memo ended with the third-party notice.
  Screenshot: `web-client-screenshots/advisor-live-desktop.png`, taken before the drawer moved
  beside the page on wide screens.
