"""create stories

Revision ID: aaca0e4a0f34
Revises: c9f6a4b2d3e5
Create Date: 2026-11-24 14:29:41

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "aaca0e4a0f34"
down_revision: str | Sequence[str] | None = "c9f6a4b2d3e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("character_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("body", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "content_warnings",
            postgresql.ARRAY(sa.String(length=20)),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("content_note", sa.String(length=200), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hidden_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "content_warnings <@ ARRAY['violence', 'death', 'torture', 'sexual_themes', 'abuse', 'self_harm', 'addiction', 'phobia']::varchar[]",
            name=op.f("ck_stories_content_warnings"),
        ),
        sa.CheckConstraint(
            "char_length(title) >= 1", name=op.f("ck_stories_title_length")
        ),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["characters.id"],
            name=op.f("fk_stories_character_id_characters"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_stories_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_stories")),
    )
    op.create_index(
        op.f("ix_stories_character_id"), "stories", ["character_id"], unique=False
    )
    op.create_index("ix_stories_published", "stories", ["published_at"], unique=False)
    op.create_index(op.f("ix_stories_user_id"), "stories", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_stories_user_id"), table_name="stories")
    op.drop_index("ix_stories_published", table_name="stories")
    op.drop_index(op.f("ix_stories_character_id"), table_name="stories")
    op.drop_table("stories")
