from __future__ import annotations

from sqlalchemy import select

from app.db import get_session
from app.models import Newsletter
from app.schemas import NewsletterDetail, NewsletterSummary


def _detail(n: Newsletter) -> NewsletterDetail:
    return NewsletterDetail(
        id=n.id,
        subject=n.subject,
        intro=n.intro,
        articles=n.articles,
        jobs=n.jobs,
        events=n.events,
        sent_at=n.sent_at,
        sent_to=n.sent_to,
    )


async def list_newsletters(limit: int = 20) -> list[NewsletterSummary]:
    """List past newsletter issues that have been sent, most recent first."""
    limit = max(1, min(limit, 50))
    async with get_session() as session:
        stmt = (
            select(Newsletter)
            .where(Newsletter.sent_at.isnot(None))
            .order_by(Newsletter.sent_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return [
            NewsletterSummary(id=n.id, subject=n.subject, sent_at=n.sent_at, sent_to=n.sent_to)
            for n in result.scalars().all()
        ]


async def get_newsletter(newsletter_id: int) -> NewsletterDetail | None:
    """Fetch the full content (articles, jobs, events) of a newsletter issue by id."""
    async with get_session() as session:
        n = await session.get(Newsletter, newsletter_id)
        return _detail(n) if n else None


async def get_latest_newsletter() -> NewsletterDetail | None:
    """Fetch the most recently sent newsletter issue, in full."""
    async with get_session() as session:
        stmt = (
            select(Newsletter)
            .where(Newsletter.sent_at.isnot(None))
            .order_by(Newsletter.sent_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        n = result.scalars().first()
        return _detail(n) if n else None
