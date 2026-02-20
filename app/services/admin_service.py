from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import BlogPost, FloorPlanPin, FloorPlanPinImage, Portfolio
from app.schemas.admin import (
    AdminBlogPostCreate,
    AdminBlogPostUpdate,
    AdminFloorPlanPinCreate,
    AdminFloorPlanPinResponse,
    AdminFloorPlanPinUpdate,
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


def _replace_pin_images(db: Session, pin_id: int, side: str, urls: list[str]) -> None:
    db.query(FloorPlanPinImage).filter(
        FloorPlanPinImage.floor_plan_pin_id == pin_id, FloorPlanPinImage.image_side == side
    ).delete(synchronize_session=False)
    for idx, url in enumerate(urls, start=1):
        if not url.strip():
            continue
        db.add(
            FloorPlanPinImage(
                floor_plan_pin_id=pin_id,
                image_side=side,
                image_url=url.strip(),
                sort_order=idx,
            )
        )


def _pin_response(row: FloorPlanPin) -> AdminFloorPlanPinResponse:
    before = sorted((x for x in row.images if x.image_side == "before"), key=lambda x: (x.sort_order, x.id))
    after = sorted((x for x in row.images if x.image_side == "after"), key=lambda x: (x.sort_order, x.id))
    return AdminFloorPlanPinResponse(
        pin_id=row.id,
        portfolio_id=row.portfolio_id,
        x_ratio=float(row.x_ratio),
        y_ratio=float(row.y_ratio),
        title=row.title,
        sort_order=row.sort_order,
        before_image_urls=[x.image_url for x in before],
        after_image_urls=[x.image_url for x in after],
    )


def list_floor_plan_pins(db: Session, portfolio_id: int) -> list[AdminFloorPlanPinResponse]:
    rows = (
        db.query(FloorPlanPin)
        .filter(FloorPlanPin.portfolio_id == portfolio_id)
        .order_by(FloorPlanPin.sort_order.asc(), FloorPlanPin.id.asc())
        .all()
    )
    return [_pin_response(row) for row in rows]


def create_floor_plan_pin(
    db: Session, portfolio_id: int, payload: AdminFloorPlanPinCreate
) -> AdminFloorPlanPinResponse:
    pin = FloorPlanPin(
        portfolio_id=portfolio_id,
        x_ratio=payload.x_ratio,
        y_ratio=payload.y_ratio,
        title=payload.title,
        sort_order=payload.sort_order,
    )
    db.add(pin)
    db.flush()
    _replace_pin_images(db, pin.id, "before", payload.before_image_urls)
    _replace_pin_images(db, pin.id, "after", payload.after_image_urls)
    db.commit()
    db.refresh(pin)
    return _pin_response(pin)


def update_floor_plan_pin(
    db: Session, pin_id: int, payload: AdminFloorPlanPinUpdate
) -> AdminFloorPlanPinResponse | None:
    pin = db.get(FloorPlanPin, pin_id)
    if pin is None:
        return None

    data = payload.model_dump(exclude_unset=True)
    before_urls = data.pop("before_image_urls", None)
    after_urls = data.pop("after_image_urls", None)
    for key, value in data.items():
        setattr(pin, key, value)

    if before_urls is not None:
        _replace_pin_images(db, pin_id, "before", before_urls)
    if after_urls is not None:
        _replace_pin_images(db, pin_id, "after", after_urls)

    db.commit()
    db.refresh(pin)
    return _pin_response(pin)


def delete_floor_plan_pin(db: Session, pin_id: int) -> bool:
    pin = db.get(FloorPlanPin, pin_id)
    if pin is None:
        return False
    db.delete(pin)
    db.commit()
    return True


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
