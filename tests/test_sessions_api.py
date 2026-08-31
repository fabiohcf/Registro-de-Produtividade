#app/tests/test_sessions_api_v2.py

from datetime import datetime, timezone
import uuid
import pytest
from werkzeug.security import generate_password_hash
from decimal import Decimal
from app.models.session import Session
from app.models.user import User


# ==========================================================
# Fixtures
# ==========================================================



# ==========================================================
# START SESSION
# ==========================================================

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


# ======================================================
# PAUSE
# ======================================================

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



# ======================================================
# RESUME
# ======================================================

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


# ======================================================
# FINISH
# ======================================================

def test_finish_running_session(authenticated_client, db_session, test_user):
    """Deve finalizar uma sessão em execução."""

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
        "/api/sessions/finish",
        json={"session_id": session.id},
    )

    assert response.status_code == 200

    db_session.refresh(session)

    assert session.status == "finished"
    assert session.finished_at is not None
    assert session.duration_hours >= Decimal("0")


def test_finish_paused_session(authenticated_client, db_session, test_user):
    """Deve finalizar uma sessão pausada."""

    now = datetime.now(timezone.utc)

    session = Session(
        user_id=test_user.id,
        session_type="study",
        status="paused",
        started_at=now,
        paused_at=now,
        paused_seconds=10,
        duration_hours=Decimal("0"),
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.post(
        "/api/sessions/finish",
        json={"session_id": session.id},
    )

    assert response.status_code == 200

    db_session.refresh(session)

    assert session.status == "finished"
    assert session.paused_at is None
    assert session.finished_at is not None


def test_finish_finished_session(authenticated_client, db_session, test_user):
    """Não deve finalizar uma sessão já finalizada."""

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
        "/api/sessions/finish",
        json={"session_id": session.id},
    )

    assert response.status_code == 400


def test_finish_nonexistent_session(authenticated_client):
    """Não deve finalizar uma sessão inexistente."""

    response = authenticated_client.post(
        "/api/sessions/finish",
        json={"session_id": 999999},
    )

    assert response.status_code == 404


def test_finish_session_without_goal(authenticated_client, db_session, test_user):
    """
    Sessão pode ser finalizada mesmo sem meta semanal.
    """

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
        "/api/sessions/finish",
        json={
            "session_id": session.id,
        },
    )

    assert response.status_code == 200

    db_session.refresh(session)

    assert session.status == "finished"



def test_finish_other_users_session(
    authenticated_client,
    db_session,
    other_user,
):
    """
    Usuário autenticado não pode finalizar sessão
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
        "/api/sessions/finish",
        json={
            "session_id": session.id,
        },
    )

    assert response.status_code == 404

    db_session.refresh(session)

    assert session.status == "running"
    assert session.finished_at is None




# ======================================================
# CANCEL
# ======================================================

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



# ======================================================
# SET GOAL
# ======================================================

# (vazio)

# ======================================================
# LIST
# ======================================================

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