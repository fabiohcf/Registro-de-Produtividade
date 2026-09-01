#app/tests/test_sessions_api/test_sessions_api_finish.py

from datetime import datetime, timezone
from decimal import Decimal
from app.models.session import Session



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
