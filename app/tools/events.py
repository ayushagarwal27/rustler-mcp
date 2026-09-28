from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select

from app.db import get_session
from app.models import Event
from app.schemas import EventDetail, EventSummary


def _summary(e: Event) -> EventSummary:
    return EventSummary(
        id=e.id,
        title=e.title,
        city=e.city,
        region=e.region,
        country=e.country,
        online=e.online,
        start_at=e.start_at,
        end_at=e.end_at,
        organizer=e.organizer,
        tags=e.tags or [],
        url=e.url,
    )


async def search_events(
    city: str | None = None,
    country: str | None = None,
    online: bool | None = None,
    start_after: datetime | None = None,
    start_before: datetime | None = None,
    tags: list[str] | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[EventSummary]:
    """Search tech events.

    city, country: case-insensitive exact match (matches the DB's
        lower(city)/lower(country) indexes).
    online: True for online-only events, False for in-person, omit for both.
    start_after / start_before: ISO 8601 datetimes bounding start_at.
    tags: return events whose tags overlap any of these.
    limit: max results (1-50, default 20). offset: pagination offset.
    """
    limit = max(1, min(limit, 50))
    async with get_session() as session:
        stmt = select(Event)
        if city:
            stmt = stmt.where(func.lower(Event.city) == city.lower())
        if country:
            stmt = stmt.where(func.lower(Event.country) == country.lower())
        if online is not None:
            stmt = stmt.where(Event.online == online)
        if start_after:
            stmt = stmt.where(Event.start_at >= start_after)
        if start_before:
            stmt = stmt.where(Event.start_at <= start_before)
        if tags:
            stmt = stmt.where(Event.tags.overlap(tags))
        stmt = stmt.order_by(Event.start_at.asc().nulls_last()).limit(limit).offset(max(offset, 0))
        result = await session.execute(stmt)
        return [_summary(ev) for ev in result.scalars().all()]


async def get_event(event_id: str) -> EventDetail | None:
    """Fetch full details for a single event by id."""
    async with get_session() as session:
        e = await session.get(Event, event_id)
        if e is None:
            return None
        return EventDetail(
            **_summary(e).model_dump(),
            source=e.source,
            description=e.description,
            venue_name=e.venue_name,
            address=e.address,
            country_code=e.country_code,
            rsvp_count=e.rsvp_count,
        )
