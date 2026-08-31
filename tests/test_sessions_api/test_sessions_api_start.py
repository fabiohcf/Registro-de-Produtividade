#app/tests/test_sessions_api/test_sessions_api_start.py

from datetime import datetime, timezone
import uuid
import pytest
from werkzeug.security import generate_password_hash
from decimal import Decimal
from app.models.session import Session
from app.models.user import User



def test_start_session_success(authenticated_client, test_user):

    response = authenticated_client.post(
        "/api/sessions/start",
        json={
            "session_type": "study",
        },
    )

    assert response.status_code == 201

    body = response.get_json()

    assert body["message"] == "Sessão iniciada com sucesso"

    session = body["session"]

    assert session["status"] == "running"
    assert session["session_type"] == "study"
    assert session["user_id"] == test_user.id


def test_start_session_with_description(authenticated_client, test_user):

    response = authenticated_client.post(
        "/api/sessions/start",
        json={
            "session_type": "revision",
            "description": " Revisão de Direito Constitucional ",
        },
    )

    assert response.status_code == 201

    session = response.get_json()["session"]

    assert session["description"] == "Revisão de Direito Constitucional"



def test_start_invalid_session_type(authenticated_client, test_user):

    response = authenticated_client.post(
        "/api/sessions/start",
        json={
            "session_type": "invalid_type",
        },
    )

    assert response.status_code == 400



def test_start_when_active_session_exists(authenticated_client, test_user):

    response = authenticated_client.post(
        "/api/sessions/start",
        json={
            "session_type": "study",
        },
    )

    assert response.status_code == 201

    response = authenticated_client.post(
        "/api/sessions/start",
        json={
            "session_type": "revision",
        },
    )

    assert response.status_code == 400


def test_start_session_without_goal(authenticated_client, test_user):
    """
    Sessão deve ser criada normalmente sem meta semanal definida.
    """

    response = authenticated_client.post(
        "/api/sessions/start",
        json={
            "session_type": "study",
        },
    )

    assert response.status_code == 201

    session = response.get_json()["session"]

    assert session["user_id"] == test_user.id
    assert session["status"] == "running"
    assert "goal_id" not in session

def test_start_session_ignores_goal_id(authenticated_client, test_user):
    """
    Sessões não possuem mais relacionamento com metas.
    """

    response = authenticated_client.post(
        "/api/sessions/start",
        json={
            "session_type": "study",
            "goal_id": 123,
        },
    )

    assert response.status_code == 201

    session = response.get_json()["session"]

    assert "goal_id" not in session


def test_start_session_without_weekly_goal(authenticated_client, test_user):
    """
    Usuário pode iniciar sessão sem definir meta semanal.
    """

    response = authenticated_client.post(
        "/api/sessions/start",
        json={
            "session_type": "revision",
        },
    )

    assert response.status_code == 201



def test_start_session_uses_authenticated_user(
    authenticated_client,
    test_user,
):
    """
    O usuário da sessão deve ser determinado pelo JWT,
    e não pelo user_id enviado pelo cliente.
    """

    response = authenticated_client.post(
        "/api/sessions/start",
        json={
            "user_id": 999999,
            "session_type": "study",
        },
    )

    assert response.status_code == 201

    session = response.get_json()["session"]

    assert session["user_id"] == test_user.id
