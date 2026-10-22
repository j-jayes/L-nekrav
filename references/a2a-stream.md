# A2A advisor: streamed transcript (Feature 003, FR-021b and SC-006)

Recorded on 2026-10-22 against `uv run lonekrav-serve`: the real index, with `OPENROUTER_KEY` read
from `.env` and the default model `anthropic/claude-haiku-5.5`. The output below is emitted by
`scripts/a2a_stream.py`, which uses the a2a-sdk client. A2A v1.0 calls the streaming method
`SendStreamingMessage`; the handoff's `message/stream` is the 0.3 name and is not enabled.

The ad is the public example `tests/fixtures/ads/en1_backend.txt`, and the offer is made up.

## A streamed run (run 3 of 3, warm)

```text
$ uv run python scripts/a2a_stream.py --ad-file tests/fixtures/ads/en1_backend.txt \
    --background "MSc in computer science; five years as a Python backend developer in India" \
    --offer '{"monthly_salary_sek": 52000, "fte_percent": 100, "application_type": "first_permit", "filed_on": "2026-10-01"}'
GET http://localhost:8000/.well-known/agent-card.json  (18 ms)
  name=lonekrav-advisor version=0.1.0 streaming=True
  interface={'url': 'http://localhost:8000/a2a', 'protocolBinding': 'JSONRPC', 'protocolVersion': '1.0'}
  description=Reads a job ad, the applicant's background and the offer, and writes an honest-fit memo: every plausible SSYK 2012 code with its Swedish work-permit salary consequences, from Lönekrav's own data. It uses a third-party language model (via OpenRouter), which receives the ad, background and offer you send.
  skill=honest-fit-memo: Send one data part {ad, background?, offer?} (offer: monthly_salary_sek, fte_percent, application_type, filed_on, ...) or the ad as text. Streams progress, a ui_sync artifact per tool result, and a markdown memo.

SendStreamingMessage: data part with keys ['ad', 'background', 'offer']

  0.00s  task           TASK_STATE_SUBMITTED
  0.01s  status_update  TASK_STATE_WORKING Reading the job ad
  2.24s  status_update  TASK_STATE_WORKING Calling search_occupations
  3.13s  artifact_update ui_sync:search_occupations data: {"tool": "search_occupations", "result": {"honest_fit": "The SSYK code on a work-permit offer must match the duties actually performed. These are the occupations whose official descriptions best match the text, not advice on which code to choose.", "passages": [{"by": "position", "index": 0.0, "text …
  6.04s  status_update  TASK_STATE_WORKING Calling compare_occupations
  6.09s  artifact_update ui_sync:compare_occupations data: {"tool": "compare_occupations", "result": {"honest_fit": "The SSYK code on a work-permit offer must match the duties actually performed. These are the occupations whose official descriptions best match the text, not advice on which code to choose.", "columns": [{"title_en": "Software- and system dev …
 14.63s  artifact_update memo text/markdown, 2901 characters
 14.63s  status_update  TASK_STATE_COMPLETED 

```

### The memo artifact (`text/markdown`), as streamed

> ## Memo: SSYK codes for "Backend Developer (Python)", Northwind Ledger
>
> This is information, not legal advice.
>
> ### Plausible codes
>
> **2512 Mjukvaru- och systemutvecklare m.fl.** (Software- and system developers): **best fit**
> - The ad's core duties are designing, building and maintaining REST APIs, writing Python services, reviewing code, and improving PostgreSQL databases. The official description covers analysing, designing and developing IT systems, applications and databases.
> - Salary (SCB, TAB5932, 2025): median 53,500 SEK; p25 46,200 SEK.
> - Work-permit threshold: 34,470 SEK per month (90 % of the median of 38,300 SEK, in force from 16 June 2026, applied to the 1 October 2026 filing date). The tool reports no legal flags for this code.
> - **Your offer (52,000 SEK, 100 %, first permit) passes**, with a margin of 17,530 SEK (50.9 %). No warnings were raised.
>
> **2511 Systemanalytiker och IT-arkitekter m.fl.** (System analysts and ICT-architects): **weaker fit, shown for comparison**
> - The official description centres on IT strategy, business analysis, requirements and architecture. The ad is mainly hands-on development and operations, so it matches less well. It would only apply if the job's actual duties were mainly architecture or analysis.
> - Salary (SCB, TAB5932, 2025): median 56,200 SEK; p25 47,700 SEK.
> - Work-permit threshold: 34,470 SEK per month, the same as for 2512.
> - The offer also **passes** under this code, with no warnings.
>
> The search also returned 3513 Systemadministratörer (System administrators) and 2519 Övriga IT-specialister (ICT-specialist professionals not elsewhere classified). I left them out because their duties do not describe this role.
>
> ### Points to note
> - The SSYK code on a permit application must match the duties the person will actually perform. Choose the code from the real job content, not from the salary threshold. Both codes here have the same threshold, so the threshold does not favour either.
> - The 52,000 SEK offer is above both thresholds but below the 2512 median (53,500 SEK). Lönekrav does not check whether the salary matches the collective agreement or what is customary for the occupation. Check that separately.
> - The eligibility check does not assess the applicant's qualifications or experience.
>
> ### Legal sources
> - Migrationsverket: Lönekrav för arbetstillstånd (https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand), checked on 21 October 2026. This is the source for the 90 % rule and the 38,300 SEK median.
> - SCB salary figures: TAB5932, reference year 2025, fetched 20 October 2026.
>
> The SSYK code on a work-permit offer must match the duties actually performed. These are the occupations whose official descriptions best match the text, not advice on which code to choose.
>
> Written with a third-party language model (via OpenRouter), which received the ad, background and offer you sent.

```text
total 14.63 s; in tool calls 0.94 s; model and overhead 13.69 s
```

## Latency (T028, SC-006)

The same request was sent three times in a row to a freshly started server. "In tool calls" is the
gap between each "Calling <tool>" status and the event that follows it. The rest is model time
(three model rounds) plus overhead.

| Run | Total | In tool calls | Model and overhead | Note |
|---|---|---|---|---|
| 1 | 22.27 s | 7.21 s | 15.05 s | the first full-mode search loads Harrier lazily |
| 2 | 15.59 s | 1.00 s | 14.58 s | warm |
| 3 | 14.63 s | 0.94 s | 13.69 s | warm |

Once warm, a run takes about 15 s. Nearly all of it is the model: one round to choose the search,
one to choose the comparison, and about 8 s to write a memo of about 3 000 characters. Lönekrav's
own tools take about 1 s, most of it the full-mode search of a pasted ad with `parse_ad`. That is
the baseline for the 004 chat drawer. The status updates arrive within about 2 s, so the drawer can
show progress while the memo is written.

### Found while measuring: object arguments sent as text

On its first call in every run, Haiku 5.5 sent `search_occupations`' `request` argument as a JSON
string instead of an object, with a stray closing brace (`"k": 5}}`). The tool rejected it
(`Input should be a valid dictionary or instance of SearchRequest`). The model then retried
correctly, which cost one round, about 2 s. Before the fix, three runs measured 22.3 s, 15.9 s
and 18.1 s, and run 3 needed two retries. The agent loop now reads the leading JSON object from
such a string, but only for parameters whose schema is not a string
(`protocols/agent/loop.py:_decode_objects`, tested in `tests/unit/test_agent_loop.py`). The runs
above are after the fix. Claude Code, as an MCP client, sends the object correctly
(`references/mcp-claude-code.md`).

## Without a key (T024)

The server was started with an empty key, so `load_dotenv` leaves it empty:

```text
$ OPENROUTER_KEY= uv run lonekrav-serve &
$ curl -s localhost:8000/api/v1/health
{"status":"ok","models_loaded":["kblab"],"index_chunks":9554}
$ curl -s localhost:8000/.well-known/agent-card.json | jq .name
"lonekrav-advisor"
$ uv run python scripts/a2a_stream.py --ad "Backend developer building Python APIs"
GET http://localhost:8000/.well-known/agent-card.json  (13 ms)
  name=lonekrav-advisor version=0.1.0 streaming=True
  interface={'url': 'http://localhost:8000/a2a', 'protocolBinding': 'JSONRPC', 'protocolVersion': '1.0'}
  description=Reads a job ad, the applicant's background and the offer, and writes an honest-fit memo: every plausible SSYK 2012 code with its Swedish work-permit salary consequences, from Lönekrav's own data. It uses a third-party language model (via OpenRouter), which receives the ad, background and offer you send.
  skill=honest-fit-memo: Send one data part {ad, background?, offer?} (offer: monthly_salary_sek, fte_percent, application_type, filed_on, ...) or the ad as text. Streams progress, a ui_sync artifact per tool result, and a markdown memo.

SendStreamingMessage: data part with keys ['ad']

  0.00s  task           TASK_STATE_SUBMITTED
  0.00s  status_update  TASK_STATE_REJECTED Agent unavailable: no model key is configured (set OPENROUTER_KEY in .env).

total 0.00 s; in tool calls 0.00 s; model and overhead 0.00 s
```
