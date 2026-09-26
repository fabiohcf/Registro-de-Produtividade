# app/models/session.py

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    Numeric,
    String,
    CheckConstraint,
    Index,
    text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'paused', 'finished')",
            name="ck_session_status",
        ),
        CheckConstraint(
            "session_type IN ('study', 'revision', 'questions', 'essay', 'mock_exam')",
            name="ck_session_type",
        ),
        CheckConstraint(
            """
            (status = 'running' AND paused_at IS NULL AND finished_at IS NULL)
            OR
            (status = 'paused' AND paused_at IS NOT NULL AND finished_at IS NULL)
            OR
            (status = 'finished' AND paused_at IS NULL AND finished_at IS NOT NULL)
            """,
            name="ck_session_status_timestamps",
        ),
        CheckConstraint(
            "paused_seconds >= 0",
            name="ck_session_paused_seconds",
        ),
        CheckConstraint(
            "questions_total IS NULL OR questions_total >= 0",
            name="ck_session_questions_total",
        ),
        CheckConstraint(
            "questions_correct IS NULL OR questions_correct >= 0",
            name="ck_session_questions_correct",
        ),
        CheckConstraint(
            "duration_hours >= 0",
            name="ck_session_duration_hours",
        ),
        Index(
            "uq_session_active_per_user",
            "user_id",
            unique=True,
            postgresql_where=text(
                "status IN ('running', 'paused')"
            ),
            sqlite_where=text(
                "status IN ('running', 'paused')"
            ),
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    duration_hours = Column(
        Numeric(10, 4),
        nullable=False,
        default=0,
    )

    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    finished_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Status da sessão
    status = Column(
        String(20),
        nullable=False,
        default="running",
    )

    # study, revision, questions, essay, mock_exam
    session_type = Column(
        String(20),
        nullable=False,
    )

    description = Column(
        String(255),
        nullable=True,
    )

    paused_seconds = Column(
        Integer,
        nullable=False,
        default=0,
    )

    paused_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    questions_total = Column(
        Integer,
        nullable=True,
    )

    questions_correct = Column(
        Integer,
        nullable=True,
    )

    user = relationship(
        "User",
        back_populates="sessions",
    )