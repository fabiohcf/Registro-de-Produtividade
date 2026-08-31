#app/tests/test_sessions_api/test_sessions_api_cancel.py

from datetime import datetime, timezone
import uuid
import pytest
from werkzeug.security import generate_password_hash
from decimal import Decimal
from app.models.session import Session
from app.models.user import User



def test_cancel_running_session(authenticated_client, db_session, test_user):
    """Deve cancelar uma sessão em execução."""

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

    session_id = session.id

    response = authenticated_client.post(
        "/api/sessions/cancel",
        json={"session_id": session.id},
    )
    
    assert response.status_code == 200

    db_session.expire_all()

    assert db_session.get(Session, session_id) is None


def test_cancel_paused_session(authenticated_client, db_session, test_user):
    """Deve cancelar uma sessão pausada."""

    session = Session(
        user_id=test_user.id,
        session_type="study",
        status="paused",
        started_at=datetime.now(timezone.utc),
        paused_at=datetime.now(timezone.utc),
        duration_hours=Decimal("0"),
        paused_seconds=120,
    )

    db_session.add(session)
    db_session.commit()

    session_id = session.id

    response = authenticated_client.post(
        "/api/sessions/cancel",
        json={"session_id": session.id},
    )

    assert response.status_code == 200

    db_session.expire_all()

    assert db_session.get(Session, session_id) is None


def test_cancel_finished_session(authenticated_client, db_session, test_user):
    """Não deve cancelar uma sessão finalizada."""

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

    session_id = session.id

    response = authenticated_client.post(
        "/api/sessions/cancel",
        json={"session_id": session_id},
    )

    assert response.status_code == 400


def test_cancel_nonexistent_session(authenticated_client):
    """Não deve cancelar sessão inexistente."""

    response = authenticated_client.post(
        "/api/sessions/cancel",
        json={"session_id": 999999},
    )

    assert response.status_code == 404


def test_cancel_other_users_session(
    authenticated_client,
    db_session,
    other_user,
):
    """
    Usuário autenticado não pode cancelar sessão
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

    session_id = session.id

    response = authenticated_client.post(
        "/api/sessions/cancel",
        json={
            "session_id": session_id,
        },
    )

    assert response.status_code == 404

    db_session.expire_all()

    session = db_session.get(Session, session_id)

    assert session is not None
    assert session.user_id == other_user.id
    assert session.status == "running"

