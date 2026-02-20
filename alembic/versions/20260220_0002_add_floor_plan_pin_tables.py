"""add floor plan pin tables

Revision ID: 20260220_0002
Revises: 20260215_0001
Create Date: 2026-02-20 23:20:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260220_0002"
down_revision: Union[str, Sequence[str], None] = "20260215_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "floor_plan_pins",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("portfolio_id", sa.BigInteger(), nullable=False),
        sa.Column("x_ratio", sa.Numeric(5, 2), nullable=False),
        sa.Column("y_ratio", sa.Numeric(5, 2), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.CheckConstraint("x_ratio >= 0 AND x_ratio <= 100", name="ck_floor_plan_pins_x_ratio_range"),
        sa.CheckConstraint("y_ratio >= 0 AND y_ratio <= 100", name="ck_floor_plan_pins_y_ratio_range"),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_floor_plan_pins_portfolio_sort", "floor_plan_pins", ["portfolio_id", "sort_order"], unique=False)

    op.create_table(
        "floor_plan_pin_images",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("floor_plan_pin_id", sa.BigInteger(), nullable=False),
        sa.Column("image_side", sa.String(length=10), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.CheckConstraint("image_side IN ('before','after')", name="ck_floor_plan_pin_images_side"),
        sa.ForeignKeyConstraint(["floor_plan_pin_id"], ["floor_plan_pins.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_floor_plan_pin_images_pin_side_sort",
        "floor_plan_pin_images",
        ["floor_plan_pin_id", "image_side", "sort_order"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_floor_plan_pin_images_pin_side_sort", table_name="floor_plan_pin_images")
    op.drop_table("floor_plan_pin_images")
    op.drop_index("ix_floor_plan_pins_portfolio_sort", table_name="floor_plan_pins")
    op.drop_table("floor_plan_pins")
