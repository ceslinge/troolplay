"""create reports

Revision ID: 0de9f6cce6a3
Revises: 47a7e79c1204
Create Date: 2026-11-24 15:32:25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0de9f6cce6a3"
down_revision: str | Sequence[str] | None = "47a7e79c1204"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reporter_id", sa.Integer(), nullable=True),
        sa.Column("reported_user_id", sa.Integer(), nullable=True),
        sa.Column("target_character_id", sa.Integer(), nullable=True),
        sa.Column("target_story_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.String(length=20), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("decision", sa.String(length=20), nullable=True),
        sa.Column("handled_by", sa.Integer(), nullable=True),
        sa.Column("handled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "reason IN ('off_topic', 'disrespect', 'hate', 'explicit', 'personal_info', 'impersonation', 'spam', 'illegal', 'other')",
            name=op.f("ck_reports_reason"),
        ),
        sa.CheckConstraint(
            "target_character_id IS NULL OR target_story_id IS NULL",
            name=op.f("ck_reports_one_target"),
        ),
        sa.ForeignKeyConstraint(
            ["handled_by"],
            ["users.id"],
            name=op.f("fk_reports_handled_by_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reported_user_id"],
            ["users.id"],
            name=op.f("fk_reports_reported_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reporter_id"],
            ["users.id"],
            name=op.f("fk_reports_reporter_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["target_character_id"],
            ["characters.id"],
            name=op.f("fk_reports_target_character_id_characters"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["target_story_id"],
            ["stories.id"],
            name=op.f("fk_reports_target_story_id_stories"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reports")),
    )
    op.create_index(
        op.f("ix_reports_reported_user_id"),
        "reports",
        ["reported_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reports_reporter_id"), "reports", ["reporter_id"], unique=False
    )
    op.create_index(
        op.f("ix_reports_target_character_id"),
        "reports",
        ["target_character_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reports_target_story_id"), "reports", ["target_story_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_reports_target_story_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_target_character_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_reporter_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_reported_user_id"), table_name="reports")
    op.drop_table("reports")
