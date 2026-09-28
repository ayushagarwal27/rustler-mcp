from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class JobSummary(BaseModel):
    id: str
    title: str
    company: str
    location: str | None = None
    remote: str | None = None
    country: str | None = None
    tags: list[str] = []
    salary_from: int | None = None
    salary_to: int | None = None
    currency: str | None = None
    contract_type: str | None = None
    experience_level: str | None = None
    posted_at: datetime | None = None
    link: str | None = None


class JobDetail(JobSummary):
    source: str
    description: str | None = None
    about_role: str | None = None
    about_role_html: str | None = None
    requirements: list[str] = []
    nice_to_have: list[str] = []
    requirements_enriched: Any | None = None
    nice_to_have_enriched: Any | None = None
    benefits: Any | None = None
    image: str | None = None


class RepoSummary(BaseModel):
    full_name: str
    category: str | None = None
    name: str
    description: str | None = None
    url: str | None = None
    stars: int | None = None
    forks: int | None = None
    open_issues: int | None = None
    topics: list[str] = []
    owner_avatar: str | None = None
    pushed_at: datetime | None = None


class RepoIssues(BaseModel):
    repo_full_name: str
    issues: Any
    fetched_at: datetime


class EventSummary(BaseModel):
    id: str
    title: str
    city: str | None = None
    region: str | None = None
    country: str | None = None
    online: bool | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    organizer: str | None = None
    tags: list[str] = []
    url: str | None = None


class EventDetail(EventSummary):
    source: str
    description: str | None = None
    venue_name: str | None = None
    address: str | None = None
    country_code: str | None = None
    rsvp_count: int | None = None


class NewsletterSummary(BaseModel):
    id: int
    subject: str
    sent_at: datetime | None = None
    sent_to: int


class NewsletterDetail(NewsletterSummary):
    intro: str | None = None
    articles: Any
    jobs: Any
    events: Any


class IssueHit(BaseModel):
    """One issue, surfaced from a cross-repo search rather than a
    single get_repo_issues lookup."""

    repo_full_name: str
    id: int | None = None
    title: str | None = None
    url: str | None = None
    badge: str | None = None
    labels: list[str] = []
    comments: int | None = None
    created_at: str | None = None
