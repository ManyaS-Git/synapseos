"""Memory engine schema — memories, chunks, tags, relations.

Revision ID: 002_memory_engine
Revises: 001_initial_identity
Create Date: 2026-07-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_memory_engine"
down_revision: Union[str, None] = "001_initial_identity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create memory engine tables."""

    # ── Memories ─────────────────────────────────────────────────────
    op.create_table(
        "memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("embedding_id", sa.String(255), nullable=True, unique=True),
        sa.Column("memory_type", sa.String(50), nullable=False, index=True),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("source_url", sa.Text, nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, nullable=True),
        sa.Column("importance_score", sa.Float, default=0.5, nullable=False),
        sa.Column("confidence", sa.Float, default=1.0, nullable=False),
        sa.Column("status", sa.String(20), default="active", nullable=False, index=True),
        sa.Column("access_count", sa.Integer, default=0, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("accessed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── Memory Chunks ───────────────────────────────────────────────
    op.create_table(
        "memory_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "memory_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("memories.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding_id", sa.String(255), nullable=True, unique=True),
        sa.Column("token_count", sa.Integer, default=0, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── Memory Tags ─────────────────────────────────────────────────
    op.create_table(
        "memory_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "memory_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("memories.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("tag", sa.String(100), nullable=False, index=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── Memory Relations ────────────────────────────────────────────
    op.create_table(
        "memory_relations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "source_memory_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("memories.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "target_memory_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("memories.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("relation_type", sa.String(50), nullable=False),
        sa.Column("target_entity_type", sa.String(50), nullable=True),
        sa.Column("target_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, nullable=True),
        sa.Column("weight", sa.Float, default=1.0, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Composite index for tag lookups
    op.create_index(
        "ix_memory_tags_memory_tag",
        "memory_tags",
        ["memory_id", "tag"],
    )


def downgrade() -> None:
    """Drop memory engine tables."""
    op.drop_table("memory_relations")
    op.drop_table("memory_tags")
    op.drop_table("memory_chunks")
    op.drop_table("memories")
