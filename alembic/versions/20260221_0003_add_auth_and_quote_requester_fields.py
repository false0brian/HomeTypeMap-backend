"""add auth tables and quote requester fields

Revision ID: 20260221_0003
Revises: 20260220_0002
Create Date: 2026-02-21 11:40:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260221_0003"
down_revision: Union[str, Sequence[str], None] = "20260220_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_users",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("email", sa.String(length=160), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        sa.Column("user_key", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("user_key"),
    )
    op.create_index("ix_app_users_email", "app_users", ["email"], unique=False)
    op.create_index("ix_app_users_user_key", "app_users", ["user_key"], unique=False)

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["app_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"], unique=False)
    op.create_index("ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"], unique=False)

    op.add_column("quote_requests", sa.Column("requester_name", sa.String(length=80), nullable=True))
    op.add_column("quote_requests", sa.Column("requester_email", sa.String(length=160), nullable=True))


def downgrade() -> None:
    op.drop_column("quote_requests", "requester_email")
    op.drop_column("quote_requests", "requester_name")

    op.drop_index("ix_auth_sessions_expires_at", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_user_id", table_name="auth_sessions")
    op.drop_table("auth_sessions")

    op.drop_index("ix_app_users_user_key", table_name="app_users")
    op.drop_index("ix_app_users_email", table_name="app_users")
    op.drop_table("app_users")
