# Contract: MCP server

The server is at `http://localhost:8000/mcp`, using MCP's streamable HTTP transport, and is mounted
on the same app as `/api/v1` (research R2). Its server name is `lonekrav`, and its `instructions` field tells every client, before any call,
that results name their sources and that the code on an offer must match the duties actually
performed (Principle III). The machine-readable
contract is the server's own `tools/list` and `resources/list`. This file is the human-readable
index.

Add it to Claude Code with:

```bash
claude mcp add --transport http lonekrav http://localhost:8000/mcp
```

## Tools

| Tool | Arguments | Result | Matching REST route |
|---|---|---|---|
| `search_occupations` | `request: SearchRequest` (`text`, `mode` fast or full, `k` 1–20, `parse_ad`) | `SearchAnswer` | `POST /api/v1/search` |
| `extract_job_ad_signal` | `request: AdText` (`text`) | `ParsedAd` | `POST /api/v1/parse-job-ad` |
| `get_occupation_salary` | `code`, `age_band` (optional), `on` (optional ISO date, default today) | `SalaryPayload` | `GET /api/v1/occupations/{code}/salary` |
| `evaluate_permit_eligibility` | `request: EligibilityRequest` | `EligibilityAnswer` | `POST /api/v1/eligibility` |
| `compare_occupations` | `request: CompareRequest` (`codes` 2–5, optional `offer`) | `Comparison` | `POST /api/v1/compare` |

## Resources

| URI | MIME type | Content | Matching REST route |
|---|---|---|---|
| `legal://timeline` | `application/json` | `list[TimelineEvent]` as JSON | `GET /api/v1/legal/timeline` |
| `ssyk://{code}` (template) | `application/json` | `OccupationProfile` as JSON, with legal flags and without ILO text | `GET /api/v1/occupations/{code}` |

## Rules

- **Same answers**: a tool's `structuredContent` and a resource's JSON text are byte-for-byte the
  JSON of the REST response for the same input (SC-001). Their schemas come from the same core
  models (FR-008).
- **Errors**:
  - An unknown code returns a tool error (`isError: true`) with the text `unknown SSYK code '9999'`,
    the same as REST's 404 detail.
  - An unknown age band returns REST's 422 message.
  - Invalid arguments are rejected by the argument schema, and the error names the field.
  - An unexpected error gives a masked message with no path (`mask_error_details`).
- **Honest fit**: results keep `honest_fit` and `disclaimer` exactly as the core sets them.
- **No key needed**: no tool reads `OPENROUTER_KEY`.
- **No content logging**: tool arguments and results are never logged (FR-005).
