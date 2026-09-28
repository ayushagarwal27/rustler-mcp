from __future__ import annotations

from fastmcp import FastMCP

from app.config import settings
from app.tools import events, issues, jobs, newsletters, repos

mcp = FastMCP(name=settings.mcp_server_name)

# jobs
mcp.tool(jobs.search_jobs)
mcp.tool(jobs.get_job)

# github repos (curated + trending)
mcp.tool(repos.list_top_repos)
mcp.tool(repos.get_repo)
mcp.tool(repos.list_trending_repos)

# github issues
mcp.tool(issues.get_repo_issues)
mcp.tool(issues.search_repo_issues)

# events
mcp.tool(events.search_events)
mcp.tool(events.get_event)

# newsletter
mcp.tool(newsletters.list_newsletters)
mcp.tool(newsletters.get_newsletter)
mcp.tool(newsletters.get_latest_newsletter)

