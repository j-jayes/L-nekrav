# Lönekrav

Which SSYK 2012 code fits a job, and what salary does that code require for a Swedish work permit?
Lönekrav maps a job title or a pasted job ad, in any language, to the closest SSYK codes. It shows
SCB's salary distribution for each code against the statutory salary floor, and explains the rules.
It serves all of this in four ways, on one port:

| Surface | Path | For |
|---|---|---|
| Web page | `/` | People: search, salary chart, comparison, the rules and an offer calculator |
| REST | `/api/v1` (docs at `/api/v1/docs`) | Programs |
| MCP | `/mcp` | Chat assistants such as Claude Code (`claude mcp add --transport http lonekrav http://localhost:8000/mcp`) |
| A2A | `/a2a`, card at `/.well-known/agent-card.json` | Agents and the page's advisor drawer: the `lonekrav-advisor` honest-fit memo |

The framing is **honest fit**. The code on an offer must match the duties actually performed.
Lönekrav shows each plausible code and its consequences; it never recommends a code for its lower
threshold. It is information, not legal advice.

## Run it locally

You need [uv](https://docs.astral.sh/uv/), Node 22 and, for the advisor only, an
[OpenRouter](https://openrouter.ai/) key.

```bash
uv sync
uv run lonekrav-etl fetch && uv run lonekrav-etl build && uv run lonekrav-etl index   # over an hour cold
(cd frontend && npm ci && npm run build)
uv run lonekrav-serve                      # http://127.0.0.1:8000
```

For page development, run `npm run dev` in `frontend/`; it proxies the API to port 8000. The tests
are `uv run pytest` (Python) and `npm test` (the page).

## Run it in Docker

After the index is built (above), one command builds and starts everything:

```bash
docker compose up --build                  # http://localhost:8000
```

The image carries the search models and the index, so it needs no volume and downloads nothing at
start-up. A build takes a few minutes, and the container starts in about 40 seconds. Compose caps the
container at 5 GB: with both search models loaded it uses about 4.1 GiB
(`references/container-memory.md`).

## Settings

All settings are environment variables, read at start-up. Compose takes them from your shell or from
`.env`. The key is only ever passed at run time, and it is never part of the image.

| Variable | Default | What it does |
|---|---|---|
| `OPENROUTER_KEY` | unset | Enables the advisor. Without it, everything else works and the advisor says it is unavailable |
| `LONEKRAV_LLM_MODEL` | `anthropic/claude-haiku-5.5` | The advisor's model on OpenRouter |
| `LONEKRAV_PUBLIC_URL` | `http://localhost:8000` | The address in the agent card (`{value}/a2a`); set it to where clients reach the server |
| `HOST`, `PORT` | `127.0.0.1`, `8000` | Where `lonekrav-serve` listens (the image sets `HOST=0.0.0.0`) |
| `LONEKRAV_PORT` | `8000` | The host port compose publishes |
| `MILVUS_URI` | the Milvus Lite index in `data/` | A Milvus server instead of the local index |

## Cloud Run (documented, not deployed)

The same image runs on Google Cloud Run. This has not been deployed; it is the intended route.

```bash
# Cloud Run runs linux/amd64; the lock file takes CPU-only torch on Linux for either architecture.
docker buildx build --platform linux/amd64 -f docker/Dockerfile -t REGION-docker.pkg.dev/PROJECT/lonekrav/lonekrav:1 --push .
gcloud run deploy lonekrav --image REGION-docker.pkg.dev/PROJECT/lonekrav/lonekrav:1 \
  --region REGION --memory 5Gi --cpu 2 --port 8000 --min-instances 0 \
  --set-env-vars LONEKRAV_PUBLIC_URL=https://YOUR-SERVICE-URL \
  --set-secrets OPENROUTER_KEY=openrouter-key:latest
```

Notes:
- **Key**: keep `OPENROUTER_KEY` in Secret Manager, as above, not in `--set-env-vars`.
- **Private registry only**: the image's search index includes ILO ISCO-08 text, which is used
  for ranking but never shown. ILO reserves reproduction rights, so push the image only to a
  private registry such as Artifact Registry.
- **Cold starts**: a new instance takes about 40 seconds to start. The first accurate search then
  loads the second model, which takes about 10 seconds more. Set `--min-instances 1` if that
  matters.

## Data and credits

- **Salary statistics**: SCB, CC0 1.0. Credit: "Medlingsinstitutet / SCB lönestrukturstatistik
  (AM0110)".
- **Occupation codes and Swedish titles**: SCB SSYK 2012, CC0 1.0.
- **Swedish occupation names**: JobTech Taxonomy (Arbetsförmedlingen), published as open data. Its
  exact licence is not yet confirmed.
- **English descriptions**: ESCO, European Commission.
- **Legal rules**: SFS 2026:605 and Migrationsverket. Each rule carries its source and the date it
  was checked.
- **ILO ISCO-08 text**: used only inside the search index (see above). It is never stored in
  `data/processed/` or served.

The data dictionary is `data/processed/data-dict.yaml`. How the project is built is described in
`references/development-plan.md` and `specs/`.
