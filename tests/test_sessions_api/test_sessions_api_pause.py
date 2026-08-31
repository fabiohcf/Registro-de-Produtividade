#app/tests/test_sessions_api/test_sessions_api_pause.py

from datetime import datetime, timezone
import uuid
import pytest
from werkzeug.security import generate_password_hash
from decimal import Decimal
from app.models.session import Session
from app.models.user import User


def test_pause_running_session(authenticated_client, db_session, test_user):
    """Deve pausar uma sessão em execução."""

    session = Session(
        user_id=test_user.id,
        session_type="study",
        status="running",
        started_at=datetime.now(timezone.utc),
        duration_hours=Decimal("0"),
        paused_seconds=0,
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.post(
        "/api/sessions/pause",
        json={"session_id": session.id},
    )

    assert response.status_code == 200

    db_session.refresh(session)

    assert session.status == "paused"
    assert session.paused_at is not None


def test_pause_already_paused_session(authenticated_client, db_session, test_user):
    """Não deve permitir pausar uma sessão já pausada."""

    session = Session(
        user_id=test_user.id,
        session_type="study",
        status="paused",
        started_at=datetime.now(timezone.utc),
        paused_at=datetime.now(timezone.utc),
        duration_hours=Decimal("0"),
        paused_seconds=0,
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.post(
        "/api/sessions/pause",
        json={"session_id": session.id},
    )

    assert response.status_code == 400


def test_pause_finished_session(authenticated_client, db_session, test_user):
    """Não deve permitir pausar sessão finalizada."""

    now = datetime.now(timezone.utc)

    session = Session(
        user_id=test_user.id,
        session_type="study",
        status="finished",
        started_at=now,
        finished_at=now,
        duration_hours=Decimal("1"),
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.post(
        "/api/sessions/pause",
        json={"session_id": session.id},
    )

    assert response.status_code == 400


def test_pause_nonexistent_session(authenticated_client):
    """Sessão inexistente deve retornar 404."""

    response = authenticated_client.post(
        "/api/sessions/pause",
        json={"session_id": 999999},
    )

    assert response.status_code == 404


def test_pause_other_users_session(
    authenticated_client,
    db_session,
    other_user,
):
    """
    Usuário autenticado não pode pausar sessão
    pertencente a outro usuário.
    """

    session = Session(
        user_id=other_user.id,
        session_type="study",
        status="running",
        started_at=datetime.now(timezone.utc),
        duration_hours=Decimal("0"),
        paused_seconds=0,
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.post(
        "/api/sessions/pause",
        json={
            "session_id": session.id,
        },
    )

    assert response.status_code == 404

    db_session.refresh(session)

    assert session.status == "running"