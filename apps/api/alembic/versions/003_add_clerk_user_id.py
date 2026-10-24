"""Add Clerk user ID and make password_hash nullable.

Revision ID: 003_add_clerk_user_id
Revises: 002_memory_engine
Create Date: 2026-10-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003_add_clerk_user_id"
down_revision: Union[str, None] = "002_memory_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add clerk_user_id column and make password_hash nullable."""
    op.add_column("users", sa.Column("clerk_user_id", sa.String(255), nullable=True))
    op.create_index("ix_users_clerk_user_id", "users", ["clerk_user_id"], unique=True)
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=True)


def downgrade() -> None:
    """Remove clerk_user_id column and restore password_hash not null."""
    op.drop_index("ix_users_clerk_user_id", table_name="users")
    op.drop_column("users", "clerk_user_id")
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=False)
