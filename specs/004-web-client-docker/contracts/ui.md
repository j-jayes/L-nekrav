# Contract: the page

## Address

`/?view=search|compare|legal&codes=C1,C2,…&age=18-24|25-34|35-44|45-54|55-64|65-68`

- An unknown `view` falls back to `search`.
- `codes` are 4-digit SSYK codes. The chart and compare share the first four. A code
  that is unknown (a 404 from `/occupations/{code}`), a duplicate or past the limit is dropped, and
  a note names it.
- An unknown `age` is ignored, and the simulated bars stay off.
- The ad, background and offer never appear in the address.

## Views and what each shows

| View | Shows | Data from |
|---|---|---|
| search | The search box; which speed is on screen ("fast", or "accurate" plus its fallback reason); kept and set-aside passages with their reasons, and the searched text; a result list (code, sv/en title, matched passage, legal flags with sources, a score strip with one rank per method or "not run"); `honest_fit`; selection chips; the salary chart and its table; an age band picker; a simulated toggle per code | `POST /search` (fast, then full), `GET /occupations/{code}/salary?age_band=` |
| compare | One column per selected code, in selection order: sv/en tasks with source, the latest salary summary, the threshold, flags, and with an offer eligibility status, margin and warnings; `honest_fit`; the offer form | `POST /compare` |
| legal | The rules, medians, the exempt, banned and partially banned code lists, personal exemptions, the transition rule and statements, each with a source link and checked-on date; the timeline; the calculator (offer + code → eligibility answer); the disclaimer | `GET /legal/registry`, `GET /legal/timeline`, `POST /eligibility` |
| drawer (all views) | The third-party notice before the first send; ad, background and optional offer; progress lines; the memo as Markdown (no raw HTML); a Cancel button; the error or unavailable reason | `/.well-known/agent-card.json`, `/a2a` |

## Chart marks (one row per code)

| Mark | Value | Rule |
|---|---|---|
| Bar | latest distribution `p10` → `p90` | Not drawn if either end is null, and a note is shown |
| Low band | `p10` → `p25` | Shaded inside the bar, not drawn if `p25` is null |
| Median tick | `median` | |
| Age dots | `age_bands[].mean_monthly` per band (not `all`) | Null bands are omitted |
| Floor line | see data-model "Floor line" | Labelled with the rule and amount (the amount from the payload) |
| Ghost bar | `simulated.p10` → `simulated.p90` for the chosen age band | Off by default, dashed and light, labelled "simulated", with the formula and inputs on demand |
| Caption | each `source_table` and `reference_year`; credit to SCB and Medlingsinstitutet | |

Every mark's value is reachable by hover, focus and tap, and the table holds the same values.
