#app/tests/test_sessions_api/test_sessions_api_list.py

from datetime import datetime, timezone
import uuid
import pytest
from werkzeug.security import generate_password_hash
from decimal import Decimal
from app.models.session import Session
from app.models.user import User


def test_list_sessions_requires_authentication(client):
    """
    Não deve permitir listar sessões sem autenticação.
    """

    response = client.get("/api/sessions/list")

    assert response.status_code == 401


def test_authenticated_user_can_list_own_sessions(
    authenticated_client,
    test_user,
    db_session,
):
    """
    Usuário autenticado deve conseguir listar
    suas próprias sessões.
    """

    session = Session(
        user_id=test_user.id,
        session_type="study",
        status="finished",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration_hours=Decimal("1.0"),
        paused_seconds=0,
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.get(
        "/api/sessions/list"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["user_id"] == test_user.id
    assert data[0]["id"] == session.id