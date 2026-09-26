"""add session integrity constraints

Revision ID: f8de7633e97d
Revises: 8ee25d9c18e9
Create Date: 2026-09-25 18:35:02.563522

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f8de7633e97d'
down_revision: Union[str, Sequence[str], None] = '8ee25d9c18e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aplica as garantias de integridade das sessões."""

    op.alter_column(
        "sessions",
        "started_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
    )

    op.create_check_constraint(
        "ck_session_status",
        "sessions",
        "status IN ('running', 'paused', 'finished')",
    )

    op.create_check_constraint(
        "ck_session_type",
        "sessions",
        (
            "session_type IN "
            "('study', 'revision', 'questions', 'essay', 'mock_exam')"
        ),
    )

    op.create_check_constraint(
        "ck_session_status_timestamps",
        "sessions",
        """
        (status = 'running' AND paused_at IS NULL AND finished_at IS NULL)
        OR
        (status = 'paused' AND paused_at IS NOT NULL AND finished_at IS NULL)
        OR
        (status = 'finished' AND paused_at IS NULL AND finished_at IS NOT NULL)
        """,
    )

    op.create_index(
        "uq_session_active_per_user",
        "sessions",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('running', 'paused')"
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Remove as garantias de integridade adicionadas nesta revisão."""

    op.drop_index(
        "uq_session_active_per_user",
        table_name="sessions",
    )

    op.drop_constraint(
        "ck_session_status_timestamps",
        "sessions",
        type_="check",
    )

    op.drop_constraint(
        "ck_session_type",
        "sessions",
        type_="check",
    )

    op.drop_constraint(
        "ck_session_status",
        "sessions",
        type_="check",
    )

    op.alter_column(
        "sessions",
        "started_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )
    # ### end Alembic commands ###
