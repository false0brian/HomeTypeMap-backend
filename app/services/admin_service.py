from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import BlogPost, Portfolio
from app.schemas.admin import (
    AdminBlogPostCreate,
    AdminBlogPostUpdate,
    AdminPortfolioCreate,
    AdminPortfolioUpdate,
    PublishStatus,
)


def _maybe_mark_portfolio_published(row: Portfolio, status: PublishStatus) -> None:
    if status == PublishStatus.published and row.published_at is None:
        row.published_at = datetime.now(UTC)
    if status != PublishStatus.published:
        row.published_at = None


def create_admin_portfolio(db: Session, payload: AdminPortfolioCreate) -> Portfolio:
    row = Portfolio(**payload.model_dump())
    _maybe_mark_portfolio_published(row, payload.status)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_admin_portfolios(
    db: Session,
    vendor_id: int | None = None,
    status: PublishStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Portfolio]:
    stmt = select(Portfolio)
    if vendor_id is not None:
        stmt = stmt.where(Portfolio.vendor_id == vendor_id)
    if status is not None:
        stmt = stmt.where(Portfolio.status == status.value)

    rows = db.execute(
        stmt.order_by(Portfolio.created_at.desc(), Portfolio.id.desc()).limit(limit).offset(offset)
    ).scalars()
    return list(rows)


def update_admin_portfolio(db: Session, portfolio_id: int, payload: AdminPortfolioUpdate) -> Portfolio | None:
    row = db.get(Portfolio, portfolio_id)
    if row is None:
        return None

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value)

    if payload.status is not None:
        _maybe_mark_portfolio_published(row, payload.status)

    db.commit()
    db.refresh(row)
    return row


def _maybe_mark_blog_published(row: BlogPost, status: PublishStatus) -> None:
    if status == PublishStatus.published and row.published_at is None:
        row.published_at = datetime.now(UTC)
    if status != PublishStatus.published:
        row.published_at = None


def create_blog_post(db: Session, payload: AdminBlogPostCreate) -> BlogPost:
    row = BlogPost(**payload.model_dump())
    _maybe_mark_blog_published(row, payload.status)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_blog_posts(
    db: Session,
    vendor_id: int | None = None,
    status: PublishStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[BlogPost]:
    stmt = select(BlogPost)
    if vendor_id is not None:
        stmt = stmt.where(BlogPost.vendor_id == vendor_id)
    if status is not None:
        stmt = stmt.where(BlogPost.status == status.value)

    rows = db.execute(stmt.order_by(BlogPost.created_at.desc(), BlogPost.id.desc()).limit(limit).offset(offset)).scalars()
    return list(rows)


def update_blog_post(db: Session, post_id: int, payload: AdminBlogPostUpdate) -> BlogPost | None:
    row = db.get(BlogPost, post_id)
    if row is None:
        return None

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value)

    if payload.status is not None:
        _maybe_mark_blog_published(row, payload.status)

    db.commit()
    db.refresh(row)
    return row
