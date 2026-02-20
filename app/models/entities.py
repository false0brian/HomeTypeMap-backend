from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    admin_dong: Mapped[str] = mapped_column(String(120), nullable=False)
    legal_dong: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[str] = mapped_column(String(300), nullable=False)
    point = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=False)

    complexes: Mapped[list[Complex]] = relationship(back_populates="location")

    __table_args__ = (
        Index("ix_locations_point", "point", postgresql_using="gist"),
        Index("ix_locations_address", "address"),
    )


class Complex(Base):
    __tablename__ = "complexes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(300), nullable=False)
    built_year: Mapped[int | None] = mapped_column(Integer)
    household_count: Mapped[int | None] = mapped_column(Integer)
    centroid_latitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    centroid_longitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)

    location: Mapped[Location] = relationship(back_populates="complexes")
    unit_types: Mapped[list[UnitType]] = relationship(back_populates="complex", cascade="all, delete-orphan")
    portfolios: Mapped[list[Portfolio]] = relationship(back_populates="complex")

    __table_args__ = (
        Index("ix_complexes_name", "name"),
        Index("ix_complexes_address", "address"),
    )


class UnitType(Base):
    __tablename__ = "unit_types"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    complex_id: Mapped[int] = mapped_column(ForeignKey("complexes.id", ondelete="CASCADE"), nullable=False)
    exclusive_area_m2: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    supply_area_m2: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    type_code: Mapped[str | None] = mapped_column(String(20))
    room_count: Mapped[int | None] = mapped_column(Integer)
    bathroom_count: Mapped[int | None] = mapped_column(Integer)
    structure_keyword: Mapped[str | None] = mapped_column(String(50))

    complex: Mapped[Complex] = relationship(back_populates="unit_types")
    portfolios: Mapped[list[Portfolio]] = relationship(back_populates="unit_type")
    floor_plans: Mapped[list[FloorPlan]] = relationship(back_populates="unit_type")

    __table_args__ = (
        UniqueConstraint("complex_id", "exclusive_area_m2", "type_code", name="uq_unit_types_complex_area_type"),
        Index("ix_unit_types_complex_id", "complex_id"),
        Index("ix_unit_types_exclusive_area_m2", "exclusive_area_m2"),
    )


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    region: Mapped[str | None] = mapped_column(String(120))
    rating: Mapped[Decimal | None] = mapped_column(Numeric(2, 1))
    contact_url: Mapped[str | None] = mapped_column(String(300))

    portfolios: Mapped[list[Portfolio]] = relationship(back_populates="vendor")
    blog_posts: Mapped[list[BlogPost]] = relationship(back_populates="vendor")


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    complex_id: Mapped[int] = mapped_column(ForeignKey("complexes.id", ondelete="RESTRICT"), nullable=False)
    unit_type_id: Mapped[int] = mapped_column(ForeignKey("unit_types.id", ondelete="RESTRICT"), nullable=False)
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("vendors.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    before_image_url: Mapped[str | None] = mapped_column(String(500))
    after_image_url: Mapped[str | None] = mapped_column(String(500))
    work_scope: Mapped[str] = mapped_column(String(80), nullable=False)
    style: Mapped[str] = mapped_column(String(80), nullable=False)
    budget_min_krw: Mapped[int | None] = mapped_column(Integer)
    budget_max_krw: Mapped[int | None] = mapped_column(Integer)
    duration_days: Mapped[int | None] = mapped_column(Integer)
    tags: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="draft")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    complex: Mapped[Complex] = relationship(back_populates="portfolios")
    unit_type: Mapped[UnitType] = relationship(back_populates="portfolios")
    vendor: Mapped[Vendor | None] = relationship(back_populates="portfolios")
    floor_plan_pins: Mapped[list[FloorPlanPin]] = relationship(back_populates="portfolio", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "budget_min_krw IS NULL OR budget_max_krw IS NULL OR budget_min_krw <= budget_max_krw",
            name="ck_portfolios_budget_order",
        ),
        Index("ix_portfolios_complex_unit", "complex_id", "unit_type_id"),
        Index("ix_portfolios_style", "style"),
        Index("ix_portfolios_work_scope", "work_scope"),
        Index("ix_portfolios_budget_range", "budget_min_krw", "budget_max_krw"),
        Index("ix_portfolios_status", "status"),
    )


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), nullable=False, unique=True)
    excerpt: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="draft")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    vendor: Mapped[Vendor | None] = relationship(back_populates="blog_posts")

    __table_args__ = (
        Index("ix_blog_posts_vendor_id", "vendor_id"),
        Index("ix_blog_posts_status", "status"),
        Index("ix_blog_posts_published_at", "published_at"),
    )


class FloorPlan(Base):
    __tablename__ = "floor_plans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    unit_type_id: Mapped[int] = mapped_column(ForeignKey("unit_types.id", ondelete="CASCADE"), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    structure_tags: Mapped[str | None] = mapped_column(Text)
    # MVP에서는 pgvector 확장 의존성을 제거하고, 임베딩 원문(JSON/문자열) 저장만 지원한다.
    embedding: Mapped[str | None] = mapped_column(Text)

    unit_type: Mapped[UnitType] = relationship(back_populates="floor_plans")


class FloorPlanPin(Base):
    __tablename__ = "floor_plan_pins"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    x_ratio: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    y_ratio: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    title: Mapped[str | None] = mapped_column(String(120))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    portfolio: Mapped[Portfolio] = relationship(back_populates="floor_plan_pins")
    images: Mapped[list[FloorPlanPinImage]] = relationship(back_populates="pin", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("x_ratio >= 0 AND x_ratio <= 100", name="ck_floor_plan_pins_x_ratio_range"),
        CheckConstraint("y_ratio >= 0 AND y_ratio <= 100", name="ck_floor_plan_pins_y_ratio_range"),
        Index("ix_floor_plan_pins_portfolio_sort", "portfolio_id", "sort_order"),
    )


class FloorPlanPinImage(Base):
    __tablename__ = "floor_plan_pin_images"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    floor_plan_pin_id: Mapped[int] = mapped_column(ForeignKey("floor_plan_pins.id", ondelete="CASCADE"), nullable=False)
    image_side: Mapped[str] = mapped_column(String(10), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    pin: Mapped[FloorPlanPin] = relationship(back_populates="images")

    __table_args__ = (
        CheckConstraint("image_side IN ('before','after')", name="ck_floor_plan_pin_images_side"),
        Index("ix_floor_plan_pin_images_pin_side_sort", "floor_plan_pin_id", "image_side", "sort_order"),
    )


class UserFavorite(Base):
    __tablename__ = "user_favorites"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_key: Mapped[str] = mapped_column(String(80), nullable=False)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_key", "portfolio_id", name="uq_user_favorites_user_portfolio"),
        Index("ix_user_favorites_user_key", "user_key"),
    )


class QuoteRequest(Base):
    __tablename__ = "quote_requests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_key: Mapped[str] = mapped_column(String(80), nullable=False)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="SET NULL"), nullable=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)
    preferred_date: Mapped[date | None] = mapped_column(Date)
    message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
