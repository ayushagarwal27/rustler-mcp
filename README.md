# Rustler MCP

An MCP server exposing Rustler's data (jobs, GitHub repos/trending, GitHub
issues, events, newsletters) as tools, backed directly by the site's
Postgres (Neon) database.

- **MCP layer:** [FastMCP](https://gofastmcp.com) (v2 API, tested against
  fastmcp 4.0.10)
- **HTTP layer:** FastAPI, mounting FastMCP's streamable-HTTP ASGI app at `/mcp`
- **DB layer:** SQLAlchemy 2.0 (async) + asyncpg, models mirror the existing
  production schema (read-only, no migrations owned by this service)

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL (and ideally DATABASE_URL_RO)
```

Run locally:

```bash
uvicorn app.main:app --reload --port 8000
```

- Health check: `GET http://localhost:8000/health`
- MCP endpoint (streamable HTTP): `POST http://localhost:8000/mcp`

Point any MCP client (Claude, an MCP inspector, etc.) at that `/mcp` URL.
This server only speaks Streamable HTTP -- there's no stdio entrypoint.

## Use a read-only DB role (recommended)

This server talks directly to your **production** database. Since every
tool here is a `SELECT`, give it a role that can't do anything else:

```sql
CREATE ROLE rustler_mcp_ro WITH LOGIN PASSWORD 'choose-a-strong-password';
GRANT CONNECT ON DATABASE neondb TO rustler_mcp_ro;
GRANT USAGE ON SCHEMA public TO rustler_mcp_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO rustler_mcp_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO rustler_mcp_ro;
```

Put that role's connection string in `DATABASE_URL_RO` in `.env`; the app
prefers it automatically and falls back to `DATABASE_URL` if unset.

## Tools

| Tool                    | Description                                                                                                       |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `search_jobs`           | Full-text + filtered search over job postings (query, tags, remote, country, experience_level, contract_type)     |
| `get_job`               | Full detail for one job by id                                                                                     |
| `list_top_repos`        | Curated GitHub repos ranked by stars, optional category filter                                                    |
| `get_repo`              | One curated repo by (full_name, category)                                                                         |
| `list_trending_repos`   | Currently trending GitHub repos                                                                                   |
| `get_repo_issues`       | Cached open issues for one repo (exact `owner/repo`)                                                              |
| `search_repo_issues`    | Issues across multiple repos in one call -- filtered by category/stars/text match on the repo, and by issue label |
| `search_events`         | Filtered event search (city, country, online, date range, tags)                                                   |
| `get_event`             | Full detail for one event by id                                                                                   |
| `list_newsletters`      | Past newsletter issues, most recent first                                                                         |
| `get_newsletter`        | Full content of one newsletter issue by id                                                                        |
| `get_latest_newsletter` | Most recently sent newsletter, in full                                                                            |

## Open items / assumptions to double-check against real data

- **`jobs.remote`** is a free-text column (not boolean) in the schema, so
  `search_jobs(remote=...)` does an exact match. Query a few real rows to
  see what values are actually stored (`"remote"`, `"hybrid"`, `"true"`,
  etc.) and adjust if it needs to be case-insensitive or multi-value.
- **`github_issues.issues`**, **`newsletters.articles/jobs/events`**, and
  `jobs.requirements_enriched` / `nice_to_have_enriched` / `benefits` are
  all opaque JSONB blobs whose _inner_ shape wasn't in the schema dump —
  they're returned as-is (pass-through `Any`). If you want structured
  filtering (e.g. "issues labeled good-first-issue", or unwrapping a
  newsletter's article list into typed fields), share a sample row and the
  corresponding tool/schema can be tightened.
- **`subscribers`, `users`, `feedback`** tables are intentionally not
  exposed — this server is read-only over the five resources you listed.
- No auth is enforced on `/mcp`, per your call that all exposed data is
  already public on the site. If that changes, add a dependency/middleware
  check before `app.mount("/mcp", mcp_app)`.
