"""init mvp schema

Revision ID: 20260215_0001
Revises: None
Create Date: 2026-02-15 14:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography

# revision identifiers, used by Alembic.
revision: str = "20260215_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "locations",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("admin_dong", sa.String(length=120), nullable=False),
        sa.Column("legal_dong", sa.String(length=120), nullable=False),
        sa.Column("address", sa.String(length=300), nullable=False),
        sa.Column("point", Geography(geometry_type="POINT", srid=4326), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_locations_address", "locations", ["address"], unique=False)
    op.create_index("ix_locations_point", "locations", ["point"], unique=False, postgresql_using="gist")

    op.create_table(
        "complexes",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("location_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("address", sa.String(length=300), nullable=False),
        sa.Column("built_year", sa.Integer(), nullable=True),
        sa.Column("household_count", sa.Integer(), nullable=True),
        sa.Column("centroid_latitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("centroid_longitude", sa.Numeric(10, 7), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_complexes_address", "complexes", ["address"], unique=False)
    op.create_index("ix_complexes_name", "complexes", ["name"], unique=False)

    op.create_table(
        "vendors",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("region", sa.String(length=120), nullable=True),
        sa.Column("rating", sa.Numeric(2, 1), nullable=True),
        sa.Column("contact_url", sa.String(length=300), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "unit_types",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("complex_id", sa.BigInteger(), nullable=False),
        sa.Column("exclusive_area_m2", sa.Numeric(7, 2), nullable=False),
        sa.Column("supply_area_m2", sa.Numeric(7, 2), nullable=True),
        sa.Column("type_code", sa.String(length=20), nullable=True),
        sa.Column("room_count", sa.Integer(), nullable=True),
        sa.Column("bathroom_count", sa.Integer(), nullable=True),
        sa.Column("structure_keyword", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["complex_id"], ["complexes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("complex_id", "exclusive_area_m2", "type_code", name="uq_unit_types_complex_area_type"),
    )
    op.create_index("ix_unit_types_complex_id", "unit_types", ["complex_id"], unique=False)
    op.create_index("ix_unit_types_exclusive_area_m2", "unit_types", ["exclusive_area_m2"], unique=False)

    op.create_table(
        "portfolios",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("complex_id", sa.BigInteger(), nullable=False),
        sa.Column("unit_type_id", sa.BigInteger(), nullable=False),
        sa.Column("vendor_id", sa.BigInteger(), nullable=True),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("before_image_url", sa.String(length=500), nullable=True),
        sa.Column("after_image_url", sa.String(length=500), nullable=True),
        sa.Column("work_scope", sa.String(length=80), nullable=False),
        sa.Column("style", sa.String(length=80), nullable=False),
        sa.Column("budget_min_krw", sa.Integer(), nullable=True),
        sa.Column("budget_max_krw", sa.Integer(), nullable=True),
        sa.Column("duration_days", sa.Integer(), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "budget_min_krw IS NULL OR budget_max_krw IS NULL OR budget_min_krw <= budget_max_krw",
            name="ck_portfolios_budget_order",
        ),
        sa.ForeignKeyConstraint(["complex_id"], ["complexes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["unit_type_id"], ["unit_types.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_portfolios_budget_range", "portfolios", ["budget_min_krw", "budget_max_krw"], unique=False)
    op.create_index("ix_portfolios_complex_unit", "portfolios", ["complex_id", "unit_type_id"], unique=False)
    op.create_index("ix_portfolios_status", "portfolios", ["status"], unique=False)
    op.create_index("ix_portfolios_style", "portfolios", ["style"], unique=False)
    op.create_index("ix_portfolios_work_scope", "portfolios", ["work_scope"], unique=False)

    op.create_table(
        "blog_posts",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("vendor_id", sa.BigInteger(), nullable=True),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("slug", sa.String(length=140), nullable=False),
        sa.Column("excerpt", sa.String(length=500), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_blog_posts_published_at", "blog_posts", ["published_at"], unique=False)
    op.create_index("ix_blog_posts_status", "blog_posts", ["status"], unique=False)
    op.create_index("ix_blog_posts_vendor_id", "blog_posts", ["vendor_id"], unique=False)

    op.create_table(
        "floor_plans",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("unit_type_id", sa.BigInteger(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=False),
        sa.Column("structure_tags", sa.Text(), nullable=True),
        sa.Column("embedding", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["unit_type_id"], ["unit_types.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "user_favorites",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_key", sa.String(length=80), nullable=False),
        sa.Column("portfolio_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_key", "portfolio_id", name="uq_user_favorites_user_portfolio"),
    )
    op.create_index("ix_user_favorites_user_key", "user_favorites", ["user_key"], unique=False)

    op.create_table(
        "quote_requests",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_key", sa.String(length=80), nullable=False),
        sa.Column("portfolio_id", sa.BigInteger(), nullable=True),
        sa.Column("vendor_id", sa.BigInteger(), nullable=True),
        sa.Column("preferred_date", sa.Date(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("quote_requests")
    op.drop_index("ix_user_favorites_user_key", table_name="user_favorites")
    op.drop_table("user_favorites")
    op.drop_table("floor_plans")
    op.drop_index("ix_blog_posts_vendor_id", table_name="blog_posts")
    op.drop_index("ix_blog_posts_status", table_name="blog_posts")
    op.drop_index("ix_blog_posts_published_at", table_name="blog_posts")
    op.drop_table("blog_posts")
    op.drop_index("ix_portfolios_work_scope", table_name="portfolios")
    op.drop_index("ix_portfolios_style", table_name="portfolios")
    op.drop_index("ix_portfolios_status", table_name="portfolios")
    op.drop_index("ix_portfolios_complex_unit", table_name="portfolios")
    op.drop_index("ix_portfolios_budget_range", table_name="portfolios")
    op.drop_table("portfolios")
    op.drop_index("ix_unit_types_exclusive_area_m2", table_name="unit_types")
    op.drop_index("ix_unit_types_complex_id", table_name="unit_types")
    op.drop_table("unit_types")
    op.drop_table("vendors")
    op.drop_index("ix_complexes_name", table_name="complexes")
    op.drop_index("ix_complexes_address", table_name="complexes")
    op.drop_table("complexes")
    op.drop_index("ix_locations_point", table_name="locations")
    op.drop_index("ix_locations_address", table_name="locations")
    op.drop_table("locations")
