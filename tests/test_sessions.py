# tests/test_sessions.py


from datetime import datetime, timedelta, timezone
from decimal import Decimal
from app.models.session import Session
from app.routes.session_service import ensure_utc


def test_create_session(db_session, test_user):

    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(hours=1)

    sessao = Session(
        user_id=test_user.id,
        session_type="study",
        status="finished",
        started_at=start_time,
        finished_at=end_time,
        duration_hours=Decimal("1.0000"),
        paused_seconds=0,
    )

    db_session.add(sessao)
    db_session.commit()

    db_sessao = (
        db_session.query(Session)
        .filter_by(user_id=test_user.id)
        .first()
    )

    assert db_sessao is not None
    assert db_sessao.user_id == test_user.id
    assert db_sessao.session_type == "study"
    assert db_sessao.status == "finished"
    assert db_sessao.finished_at is not None

    assert ensure_utc(db_sessao.started_at) == start_time
    assert ensure_utc(db_sessao.finished_at) == end_time


def test_start_pause_resume_finish_session(authenticated_client):

    response = authenticated_client.post(
        "/api/sessions/start",
        json={
            "session_type": "study",
        },
    )

    assert response.status_code == 201

    session_id = (
        response.get_json()["session"]["id"]
    )

    response = authenticated_client.post(
        "/api/sessions/pause",
        json={
            "session_id": session_id
        },
    )

    assert response.status_code == 200

    session = response.get_json()["session"]

    assert session["status"] == "paused"

    response = authenticated_client.post(
        "/api/sessions/resume",
        json={
            "session_id": session_id
        },
    )

    assert response.status_code == 200

    session = response.get_json()["session"]

    assert session["status"] == "running"

    response = authenticated_client.post(
        "/api/sessions/finish",
        json={
            "session_id": session_id
        },
    )

    assert response.status_code == 200

    session = response.get_json()["session"]

    assert session["status"] == "finished"
    assert session["duration_hours"] >= 0

