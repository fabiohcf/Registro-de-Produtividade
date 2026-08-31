#app/tests/test_sessions_api/test_sessions_api_resume.py

from datetime import datetime, timezone
import uuid
import pytest
from werkzeug.security import generate_password_hash
from decimal import Decimal
from app.models.session import Session
from app.models.user import User


def test_resume_paused_session(authenticated_client, db_session, test_user):
    """Deve retomar uma sessão pausada."""

    paused_at = datetime.now(timezone.utc)

    session = Session(
        user_id=test_user.id,
        session_type="study",
        status="paused",
        started_at=datetime.now(timezone.utc),
        paused_at=paused_at,
        paused_seconds=0,
        duration_hours=Decimal("0"),
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.post(
        "/api/sessions/resume",
        json={"session_id": session.id},
    )

    assert response.status_code == 200

    db_session.refresh(session)

    assert session.status == "running"
    assert session.paused_at is None
    assert session.paused_seconds >= 0

def test_resume_running_session(authenticated_client, db_session, test_user):
    """Não deve retomar sessão já em execução."""

    session = Session(
        user_id=test_user.id,
        session_type="study",
        status="running",
        started_at=datetime.now(timezone.utc),
        paused_seconds=0,
        duration_hours=Decimal("0"),
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.post(
        "/api/sessions/resume",
        json={"session_id": session.id},
    )

    assert response.status_code == 400

def test_resume_finished_session(authenticated_client, db_session, test_user):
    """Não deve retomar sessão finalizada."""

    session = Session(
        user_id=test_user.id,
        session_type="study",
        status="finished",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration_hours=Decimal("1"),
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.post(
        "/api/sessions/resume",
        json={"session_id": session.id},
    )

    assert response.status_code == 400

def test_resume_nonexistent_session(authenticated_client):
    """Não deve retomar sessão inexistente."""

    response = authenticated_client.post(
        "/api/sessions/resume",
        json={"session_id": 999999},
    )

    assert response.status_code == 404



def test_resume_other_users_session(
    authenticated_client,
    db_session,
    other_user,
):
    """
    Usuário autenticado não pode retomar sessão
    pertencente a outro usuário.
    """

    now = datetime.now(timezone.utc)

    session = Session(
        user_id=other_user.id,
        session_type="study",
        status="paused",
        started_at=now,
        paused_at=now,
        duration_hours=Decimal("0"),
        paused_seconds=0,
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.post(
        "/api/sessions/resume",
        json={
            "session_id": session.id,
        },
    )

    assert response.status_code == 404

    db_session.refresh(session)

    assert session.status == "paused"
    assert session.paused_at is not None
