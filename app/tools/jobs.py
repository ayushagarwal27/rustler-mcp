from __future__ import annotations

from sqlalchemy import func, select

from app.db import get_session
from app.models import Job
from app.schemas import JobDetail, JobSummary


def _summary(job: Job) -> JobSummary:
    return JobSummary(
        id=job.id,
        title=job.title,
        company=job.company,
        location=job.location,
        remote=job.remote,
        country=job.country,
        tags=job.tags or [],
        salary_from=job.salary_from,
        salary_to=job.salary_to,
        currency=job.currency,
        contract_type=job.contract_type,
        experience_level=job.experience_level,
        posted_at=job.posted_at,
        link=job.link,
    )


async def search_jobs(
    query: str | None = None,
    tags: list[str] | None = None,
    remote: str | None = None,
    country: str | None = None,
    experience_level: str | None = None,
    contract_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[JobSummary]:
    """Search job postings.

    query: free-text search over title, company and description (uses
        Postgres full-text search).
    tags: return jobs whose tags overlap any of these (e.g. ["rust", "backend"]).
    remote: exact match on the job's remote field (values vary by source,
        e.g. "remote", "hybrid", "onsite" -- inspect a few results first).
    country, experience_level, contract_type: exact-match filters.
    limit: max results (1-50, default 20). offset: pagination offset.
    """
    limit = max(1, min(limit, 50))
    async with get_session() as session:
        stmt = select(Job)

        if query:
            tsv = func.to_tsvector(
                "english",
                func.coalesce(Job.title, "")
                + " "
                + func.coalesce(Job.company, "")
                + " "
                + func.coalesce(Job.description, ""),
            )
            stmt = stmt.where(tsv.op("@@")(func.plainto_tsquery("english", query)))

        if tags:
            stmt = stmt.where(Job.tags.overlap(tags))
        if remote:
            stmt = stmt.where(Job.remote == remote)
        if country:
            stmt = stmt.where(Job.country == country)
        if experience_level:
            stmt = stmt.where(Job.experience_level == experience_level)
        if contract_type:
            stmt = stmt.where(Job.contract_type == contract_type)

        stmt = stmt.order_by(Job.posted_at.desc().nulls_last()).limit(limit).offset(max(offset, 0))
        result = await session.execute(stmt)
        return [_summary(j) for j in result.scalars().all()]


async def get_job(job_id: str) -> JobDetail | None:
    """Fetch full details (description, requirements, benefits, etc.) for a
    single job posting by its id."""
    async with get_session() as session:
        job = await session.get(Job, job_id)
        if job is None:
            return None
        return JobDetail(
            **_summary(job).model_dump(),
            source=job.source,
            description=job.description,
            about_role=job.about_role,
            about_role_html=job.about_role_html,
            requirements=job.requirements or [],
            nice_to_have=job.nice_to_have or [],
            requirements_enriched=job.requirements_enriched,
            nice_to_have_enriched=job.nice_to_have_enriched,
            benefits=job.benefits,
            image=job.image,
        )
