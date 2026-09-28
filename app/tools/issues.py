from __future__ import annotations

from sqlalchemy import func, or_, select

from app.db import get_session
from app.models import GithubIssues, GithubRepo
from app.schemas import IssueHit, RepoIssues


async def get_repo_issues(repo_full_name: str) -> RepoIssues | None:
    """Fetch the cached list of open issues for a repo, e.g. "rust-lang/rust".

    The `issues` field is returned as-is from the underlying JSONB column
    (a list of issue objects as scraped from GitHub). Its exact shape
    depends on the scraper -- inspect a sample result to see available
    fields (title, url, labels, etc.) before filtering client-side.
    """
    async with get_session() as session:
        row = await session.get(GithubIssues, repo_full_name)
        if row is None:
            return None
        return RepoIssues(repo_full_name=row.repo_full_name, issues=row.issues, fetched_at=row.fetched_at)


async def search_repo_issues(
    query: str | None = None,
    category: str | None = None,
    label: str | None = None,
    min_stars: int = 0,
    repo_limit: int = 10,
    limit: int = 30,
) -> list[IssueHit]:
    """Find issues across multiple repos in a single call, instead of
    needing a separate get_repo_issues call per repo.

    Use this whenever you don't already know the exact repo to look in --
    e.g. "rust issues in AI repos", "good first issues in web frameworks".
    Use get_repo_issues instead when you already know the exact
    "owner/repo" you want.

    How it works: picks candidate repos from the curated github_repos table
    (filtered by category/min_stars, and by `query` matched against the
    repo's name, description and topics), then pulls each candidate's
    cached issues and flattens them into one list, most recently created
    first.

    query: matched against repo name/description/topics (not issue titles).
    category: exact match on the repo's category, e.g. "ai", "cli".
    label: case-insensitive substring match against issue label names,
        e.g. "good first issue", "help wanted", "bug".
    min_stars: only consider repos with at least this many stars.
    repo_limit: how many candidate repos to scan (1-25, default 10) -- keep
        this small, since each candidate's full issue list gets pulled.
    limit: max issues to return overall (1-100, default 30).
    """
    repo_limit = max(1, min(repo_limit, 25))
    limit = max(1, min(limit, 100))

    async with get_session() as session:
        repo_stmt = select(GithubRepo.full_name)
        if category:
            repo_stmt = repo_stmt.where(GithubRepo.category == category)
        if min_stars:
            repo_stmt = repo_stmt.where(GithubRepo.stars >= min_stars)
        if query:
            like = f"%{query}%"
            repo_stmt = repo_stmt.where(
                or_(
                    GithubRepo.name.ilike(like),
                    GithubRepo.description.ilike(like),
                    GithubRepo.full_name.ilike(like),
                    func.array_to_string(GithubRepo.topics, " ").ilike(like),
                )
            )
        repo_stmt = repo_stmt.order_by(GithubRepo.stars.desc()).limit(repo_limit)
        candidate_names = [row[0] for row in (await session.execute(repo_stmt)).all()]

        if not candidate_names:
            return []

        issues_stmt = select(GithubIssues).where(GithubIssues.repo_full_name.in_(candidate_names))
        rows = (await session.execute(issues_stmt)).scalars().all()

    label_needle = label.lower() if label else None
    hits: list[IssueHit] = []

    for row in rows:
        for issue in row.issues or []:
            labels = [lbl.get("name", "") for lbl in (issue.get("labels") or [])]
            if label_needle and not any(label_needle in lbl.lower() for lbl in labels):
                continue
            hits.append(
                IssueHit(
                    repo_full_name=row.repo_full_name,
                    id=issue.get("id"),
                    title=issue.get("title"),
                    url=issue.get("url"),
                    badge=issue.get("badge"),
                    labels=labels,
                    comments=issue.get("comments"),
                    created_at=issue.get("created_at"),
                )
            )

    hits.sort(key=lambda h: h.created_at or "", reverse=True)
    return hits[:limit]
