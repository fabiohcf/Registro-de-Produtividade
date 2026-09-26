# tests/test_session_constraints.py

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.session import Session


def test_database_rejects_invalid_session_status(
    db_session,
    test_user,
):
    """
    O banco deve rejeitar status fora do domínio persistido.
    """

    session = Session(
        user_id=test_user.id,
        session_type="study",
        status="invalid_status",
        started_at=datetime.now(timezone.utc),
        duration_hours=Decimal("0"),
        paused_seconds=0,
    )

    db_session.add(session)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_database_rejects_invalid_session_type(
    db_session,
    test_user,
):
    """
    O banco deve rejeitar tipos de sessão fora do domínio.
    """

    session = Session(
        user_id=test_user.id,
        session_type="invalid_type",
        status="running",
        started_at=datetime.now(timezone.utc),
        duration_hours=Decimal("0"),
        paused_seconds=0,
    )

    db_session.add(session)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_database_rejects_session_without_started_at(
    db_session,
    test_user,
):
    """
    Toda sessão persistida deve possuir instante de início.
    """

    session = Session(
        user_id=test_user.id,
        session_type="study",
        status="running",
        started_at=None,
        duration_hours=Decimal("0"),
        paused_seconds=0,
    )

    db_session.add(session)

    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.parametrize(
    (
        "status",
        "paused_at",
        "finished_at",
    ),
    [
        ("running", datetime.now(timezone.utc), None),
        ("running", None, datetime.now(timezone.utc)),
        ("paused", None, None),
        (
            "paused",
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        ),
        ("finished", None, None),
        (
            "finished",
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        ),
    ],
)
def test_database_rejects_inconsistent_status_timestamps(
    db_session,
    test_user,
    status,
    paused_at,
    finished_at,
):
    """
    O banco deve rejeitar timestamps incompatíveis
    com o estado persistido da sessão.
    """

    session = Session(
        user_id=test_user.id,
        session_type="study",
        status=status,
        started_at=datetime.now(timezone.utc),
        paused_at=paused_at,
        finished_at=finished_at,
        duration_hours=Decimal("0"),
        paused_seconds=0,
    )

    db_session.add(session)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_database_rejects_multiple_active_sessions_for_same_user(
    db_session,
    test_user,
):
    """
    O banco deve impedir mais de uma sessão ativa
    para o mesmo usuário.
    """

    first_session = Session(
        user_id=test_user.id,
        session_type="study",
        status="running",
        started_at=datetime.now(timezone.utc),
        duration_hours=Decimal("0"),
        paused_seconds=0,
    )

    second_session = Session(
        user_id=test_user.id,
        session_type="revision",
        status="paused",
        started_at=datetime.now(timezone.utc),
        paused_at=datetime.now(timezone.utc),
        duration_hours=Decimal("0"),
        paused_seconds=0,
    )

    db_session.add(first_session)
    db_session.commit()

    db_session.add(second_session)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_database_allows_multiple_finished_sessions_for_same_user(
    db_session,
    test_user,
):
    """
    O banco deve permitir múltiplas sessões finalizadas
    para o mesmo usuário.
    """

    now = datetime.now(timezone.utc)

    first_session = Session(
        user_id=test_user.id,
        session_type="study",
        status="finished",
        started_at=now,
        finished_at=now,
        duration_hours=Decimal("0"),
        paused_seconds=0,
    )

    second_session = Session(
        user_id=test_user.id,
        session_type="revision",
        status="finished",
        started_at=now,
        finished_at=now,
        duration_hours=Decimal("0"),
        paused_seconds=0,
    )

    db_session.add_all(
        [
            first_session,
            second_session,
        ]
    )

    db_session.commit()

    assert first_session.id is not None
    assert second_session.id is not None