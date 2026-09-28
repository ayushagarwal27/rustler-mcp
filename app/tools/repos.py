from __future__ import annotations

from typing import Any

from sqlalchemy import select

from app.db import get_session
from app.models import GithubRepo, GithubTrending
from app.schemas import RepoSummary


def _summary(row: Any) -> RepoSummary:
    return RepoSummary(
        full_name=row.full_name,
        category=getattr(row, "category", None),
        name=row.name,
        description=row.description,
        url=row.url,
        stars=row.stars,
        forks=row.forks,
        open_issues=getattr(row, "open_issues", None),
        topics=row.topics or [],
        owner_avatar=row.owner_avatar,
        pushed_at=row.pushed_at,
    )


async def list_top_repos(category: str | None = None, min_stars: int = 0, limit: int = 20) -> list[RepoSummary]:
    """List curated/ranked GitHub repos, ordered by stars descending.

    category: filter to one category (e.g. "web-frameworks"); omit to see
        all categories. min_stars: only repos with at least this many stars.
    """
    limit = max(1, min(limit, 50))
    async with get_session() as session:
        stmt = select(GithubRepo)
        if category:
            stmt = stmt.where(GithubRepo.category == category)
        if min_stars:
            stmt = stmt.where(GithubRepo.stars >= min_stars)
        stmt = stmt.order_by(GithubRepo.category, GithubRepo.stars.desc()).limit(limit)
        result = await session.execute(stmt)
        return [_summary(r) for r in result.scalars().all()]


async def get_repo(full_name: str, category: str) -> RepoSummary | None:
    """Fetch a single curated repo by its full_name (e.g. "rust-lang/rust")
    and category composite key."""
    async with get_session() as session:
        repo = await session.get(GithubRepo, {"full_name": full_name, "category": category})
        return _summary(repo) if repo else None


async def list_trending_repos(limit: int = 20) -> list[RepoSummary]:
    """List currently trending GitHub repos, ordered by stars descending."""
    limit = max(1, min(limit, 50))
    async with get_session() as session:
        stmt = select(GithubTrending).order_by(GithubTrending.stars.desc()).limit(limit)
        result = await session.execute(stmt)
        return [_summary(r) for r in result.scalars().all()]
