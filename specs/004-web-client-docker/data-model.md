# Data model: Lönekrav web client and container

Feature 004 adds no domain entities. The page's types are generated from the API's OpenAPI schema
(`frontend/src/api/schema.d.ts`), so `SearchAnswer`, `SalaryPayload`, `Comparison`,
`EligibilityAnswer`, `TimelineEvent` and `Registry` are the core pydantic models and are not
redefined. The page-only state is below. It lives in memory, and partly in the query string.

## Page state (frontend only)

| State | Fields | Rules | In the address? |
|---|---|---|---|
| `View` | `"search" \| "compare" \| "legal"` | Defaults to `search`, and an unknown value falls back to it | `view` |
| `Selection` | ordered `codes: string[]`, with `payloads: Record<code, SalaryPayload>`, `simulated: Record<code, boolean>` and `ageBand: AgeBand \| null` | At most 4 codes on the chart and 5 in compare. Adding a duplicate is a no-op with a note. Advisor selections past the limit keep the 4 most recent. A code is valid only if `/occupations/{code}` answers 200 | `codes` (comma-separated), `age` |
| `SearchSession` | `text`, `fast: SearchAnswer \| null`, `full: SearchAnswer \| null`, `shown: "fast" \| "full" \| null`, `pending: {fast?: AbortController, full?: timer+AbortController}` | An answer is kept only if `answer.forText === text`. A full answer replaces a fast one. `parseAd = lines > 1 \|\| words > 40` (R5) | no |
| `OfferDraft` | the `Offer` fields (`monthly_salary_sek`, `fte_percent`, `application_type`, `filed_on`, `decided_on?`, `current_permit_granted_on?`, `exemptions[]`) | Validated by the API (422 detail mapped to fields). Shared by compare, the calculator, the chart's floor line and the drawer | no |
| `AdvisorRun` | `taskId`, `state` (`submitted`, `working`, `completed`, `failed`, `rejected`, `canceled`, `lost`), `progress: string[]`, `artifacts: UiSync[]`, `memo: string \| null`, `error: string \| null` | One run at a time. A new send while one is running is refused, and Cancel calls `CancelTask` | no |
| `AgentStatus` | `available: boolean`, `notice: string` from the card description | Read once from `/.well-known/agent-card.json`. No key gives `rejected` on the first send; the drawer then shows the server's reason | no |

## Floor line for a chart row

A floor line is drawn only when one of these gives it:

1. With an offer entered, the code's eligibility answer gives `rule_id` and `threshold_sek`.
   `status: not_permitted` means no line is drawn and a "permits cannot be granted" note is shown.
2. Otherwise, the salary payload's `thresholds` entry whose `rule_id == applicable_rule_id` gives
   the line. `applicable_rule_id: null` (a banned code) means no line, and a note is shown.

The page never chooses a rule itself.

## Deployment settings (container)

| Variable | Default | Read by | Notes |
|---|---|---|---|
| `OPENROUTER_KEY` | unset | `create_app` | At run time only, from compose interpolation of the shell or `.env`. Never in the image |
| `LONEKRAV_LLM_MODEL` | `anthropic/claude-haiku-5.5` | `create_app` | Unchanged from 003 |
| `LONEKRAV_PUBLIC_URL` | `http://localhost:8000` | `add_a2a` | The card's interface URL is `{value}/a2a` |
| `HOST` | `127.0.0.1` (the image sets `0.0.0.0`) | `main()` | |
| `PORT` | `8000` | `main()` | Cloud Run sets it |
| `MILVUS_URI` | unset (the Lite file in the image) | `core.store` | Unchanged |
| `HF_HOME`, `HF_HUB_OFFLINE` | `/models`, `1` in the image | sentence-transformers | Models are downloaded at build time |
