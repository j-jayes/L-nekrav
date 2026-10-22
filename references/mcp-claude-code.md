# MCP from Claude Code: transcript (Feature 003, FR-021a)

Recorded on 2026-10-22 against `uv run lonekrav-serve` (real index, 9 554 chunks, no
`OPENROUTER_KEY`). The events below are generated from Claude Code's `stream-json` output. Tool
results are cut to 400 characters; everything else is as returned.

## Register and connect

```text
$ claude mcp add --transport http lonekrav http://localhost:8000/mcp
Added HTTP MCP server lonekrav with URL: http://localhost:8000/mcp to local config
$ claude mcp list | grep lonekrav
lonekrav: http://localhost:8000/mcp (HTTP) - ✔ Connected
```

## Call two tools from a Claude Code session

```text
$ claude -p "Use the lonekrav MCP tools only. First call search_occupations with the text
  'Backend developer building Python APIs and maintaining our cloud services' (fast mode). Then
  call get_occupation_salary for the top code. Report the top three codes with their titles, the
  SCB table and reference year of the latest salary figures, the applicable threshold, and quote
  the honest_fit text verbatim. Keep it short." \
  --allowedTools "mcp__lonekrav__search_occupations,mcp__lonekrav__get_occupation_salary" \
  --output-format stream-json --verbose
```

```text
init: lonekrav connected
init: tools ['mcp__lonekrav__compare_occupations', 'mcp__lonekrav__evaluate_permit_eligibility', 'mcp__lonekrav__extract_job_ad_signal', 'mcp__lonekrav__get_occupation_salary', 'mcp__lonekrav__search_occupations']
tool_use mcp__lonekrav__search_occupations {"request": {"text": "Backend developer building Python APIs and maintaining our cloud services", "mode": "fast"}}
tool_result {"mode_used":"fast","fallback_reason":null,"searched_text":"Backend developer building Python APIs and maintaining our cloud services","title_list":null,"passages":null,"low_confidence":true,"hits":[{"code":"3112","title_sv":"Ingenjörer och tekniker inom bygg och anläggning","title_en":"Construction and manufacturing engineering technicians","scores":{"kblab":0.46711912751197815,"bm25":15.45087814 …
tool_use mcp__lonekrav__get_occupation_salary {"code": "3112"}
tool_result {"code":"3112","title_sv":"Ingenjörer och tekniker inom bygg och anläggning","title_en":"Construction and manufacturing engineering technicians","distributions":[{"code":"3112","year":2014,"mean":36600,"median":35000,"p10":27600,"p25":30000,"p75":41100,"p90":47900,"mean_ci95":null,"median_ci95":null,"p10_ci95":null,"p25_ci95":null,"p75_ci95":null,"p90_ci95":null,"source_table":"TAB4265","reference …
result: success, 19.4 s in the session, 4 turns
```

## Claude Code's answer

> The search returned the wrong occupations. It flagged `low_confidence: true`, and all of its top codes are construction occupations. The right code for this description is probably 2512 (software and systems developers), and it wasn't in the five results.
>
> **Top three codes (fast mode)**
> 1. **3112**: Ingenjörer och tekniker inom bygg och anläggning / Construction and manufacturing engineering technicians
> 2. **7116**: Ställningsbyggare / Scaffold builders
> 3. **2161**: Arkitekter m.fl. / Architects
>
> **Salary for 3112 (the top hit)**
> - **Latest figures:** SCB table **TAB5932**, reference year **2025**. The median is 49 400 SEK. The age-band figures come from TAB5844, also 2025.
> - **Applicable threshold:** `salary_90` (90 % of the SCB median of 38 300 SEK for 2025), which is **34 470 SEK** a month, in force on 2026-10-22.
>
> **honest_fit**
> > "The SSYK code on a work-permit offer must match the duties actually performed. These are the occupations whose official descriptions best match the text, not advice on which code to choose."
>
> I'd treat this as a search-quality bug. Running the same text in full mode should show whether this is a weakness of fast mode alone, and the query is worth adding to the benchmark as a regression case.

## Same answer over REST, and a fast-mode miss found along the way

The MCP tool returned exactly what REST returns for the same request (tests/integration/test_mcp.py asserts this for every tool). The construction codes are therefore the search's answer, not an MCP fault. Full mode, and fast mode with a shorter query, both rank 2512 first:

```text
$ curl -s -X POST localhost:8000/api/v1/search -d '{"text": "Backend developer building Python APIs and maintaining our cloud services", "mode": "fast"}'
mode_used fast | low_confidence True | top 5 ['3112', '7116', '2161', '7111', '7119']
$ curl -s -X POST localhost:8000/api/v1/search -d '{"text": "Backend developer building Python APIs and maintaining our cloud services", "mode": "full"}'
mode_used full | low_confidence True | top 5 ['2512', '2161', '3511', '7111', '3513']
$ curl -s -X POST localhost:8000/api/v1/search -d '{"text": "backend developer"}'
mode_used fast | low_confidence False | top 5 ['2512', '2513', '2143', '3449', '1331']
```

Fast mode gets this sentence wrong, though it does flag `low_confidence`. It is a Feature 002 search-quality issue and is tracked as a leftover rather than fixed in 003. It is a good case to add to the benchmark.

Timing: the whole `claude -p` call took 24.6 s wall-clock (19.4 s in the session, which includes Claude Code's own model turns). On the server, the access log shows these
times for the two tool calls. It logs only the method, path, status and time, never the tool
name or arguments (FR-005):

```text
2026-10-22 10:55:23,884 lonekrav.access POST /mcp 200 1310.4ms   # search_occupations, the first search after start-up (cold)
2026-10-22 10:55:26,905 lonekrav.access POST /mcp 200 24.2ms     # get_occupation_salary
```
