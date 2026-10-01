# Rustler MCP

An MCP server exposing Rustler's data (jobs, GitHub repos/trending, GitHub
issues, events, newsletters) as tools, backed directly by the site's
Postgres (Neon) database.

## Things you can ask it

Rustler MCP turns Rust job listings, trending/curated GitHub repos, open
issues, meetups/events, and newsletter archives into things you can just
ask for in plain English -- no need to browse the site or dig through
filters.

### Jobs

- "Find senior remote Rust jobs in the US"
- "Show me full details on job li:4471308700"

### GitHub repos

- "What are the top 5 AI category repos on Rustler?"
- "What's trending in Rust right now?"
- "Get me the full details on meilisearch/meilisearch in the AI category"

### Issues

- "What issues are open on rust-lang/rust?"
- "Find good-first-issues across the top CLI tool repos"

### Events

- "Any Rust meetups happening in Stockholm?"
- "Show me online-only Rust events coming up"

### Newsletters

- "What's in the latest Rustler newsletter?"
- "List the last 3 newsletters sent"
- "Get the full content of newsletter #23"

### Mixing it up

- "Give me a quick roundup: top trending Rust repo, one open remote Rust job, and any upcoming Rust events"

Being specific (naming a repo, city, or id) gets you a faster, single-shot
answer. Vague queries still work, but the assistant may need a couple of
tool calls to narrow things down.

## Connect to a client

The hosted server lives at:

```text
https://mcp.rustler.in/mcp/
```

It only speaks Streamable HTTP, so point any MCP-compatible client at that
URL -- no API key or local install required.

### Claude (Desktop / web)

1. Go to **Settings -> Connectors -> Add custom connector**.
2. Paste `https://mcp.rustler.in/mcp/` as the URL and save.
3. Rustler's tools will now show up as available tools in new chats.

### Claude Code (CLI)

```bash
claude mcp add --transport http rustler https://mcp.rustler.in/mcp/
```

Then start a session and ask Claude Code anything from the list above.

### ChatGPT

1. Go to **Settings -> Connectors** and choose to add a custom connector
   (this requires a plan/workspace with developer mode or custom connectors
   enabled).
2. Enter `https://mcp.rustler.in/mcp/` as the MCP server URL.
3. Enable the connector in a chat to start using it.

### Cursor

Add to `~/.cursor/mcp.json` (or **Settings -> MCP -> New MCP Server**):

```json
{
  "mcpServers": {
    "rustler": {
      "url": "https://mcp.rustler.in/mcp/"
    }
  }
}
```

### VS Code (Copilot Chat, agent mode)

Add to `.vscode/mcp.json` in your workspace (or run **MCP: Add Server**
from the Command Palette and choose HTTP):

```json
{
  "servers": {
    "rustler": {
      "type": "http",
      "url": "https://mcp.rustler.in/mcp/"
    }
  }
}
```

## Tech stack

- **MCP layer:** [FastMCP](https://gofastmcp.com) (v2 API, tested against
  fastmcp 4.0.10)
- **HTTP layer:** FastAPI, mounting FastMCP's streamable-HTTP ASGI app at `/mcp`
- **DB layer:** SQLAlchemy 2.0 (async) + asyncpg, models mirror the existing
  production schema (read-only, no migrations owned by this service)

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
