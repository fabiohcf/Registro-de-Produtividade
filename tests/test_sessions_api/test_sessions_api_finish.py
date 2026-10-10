#app/tests/test_sessions_api/test_sessions_api_finish.py

import pytest

from datetime import datetime, timezone
from decimal import Decimal
from app.models.session import Session


@pytest.mark.parametrize(
    "questions_total",
    [
        -1,
        1.5,
        "10",
        True,
    ],
)
def test_finish_question_session_with_invalid_total(
    authenticated_client,
    db_session,
    test_user,
    questions_total,
):
    """
    Não deve finalizar sessão de questões quando
    questions_total não for um inteiro positivo válido.
    """

    session = Session(
        user_id=test_user.id,
        session_type="questions",
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
            "questions_total": questions_total,
        },
    )

    assert response.status_code == 400

    db_session.refresh(session)

    assert session.status == "running"


@pytest.mark.parametrize(
    "questions_correct",
    [
        -1,
        1.5,
        "5",
        True,
    ],
)
def test_finish_question_session_with_invalid_correct(
    authenticated_client,
    db_session,
    test_user,
    questions_correct,
):
    """
    Não deve finalizar sessão de questões quando
    questions_correct não for um inteiro não negativo válido.
    """

    session = Session(
        user_id=test_user.id,
        session_type="questions",
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
            "questions_total": 10,
            "questions_correct": questions_correct,
        },
    )

    assert response.status_code == 400

    db_session.refresh(session)

    assert session.status == "running"


@pytest.mark.parametrize(
    "payload",
    [
        {"questions_total": 10},
        {"questions_correct": 5},
        {"questions_total": None},
        {"questions_correct": None},
        {
            "questions_total": 10,
            "questions_correct": 5,
        },
    ],
)
def test_finish_non_question_session_rejects_question_fields(
    authenticated_client,
    db_session,
    test_user,
    payload,
):
    """
    Sessões que não são de questões não devem aceitar
    campos específicos de questões no payload.
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
            **payload,
        },
    )

    assert response.status_code == 400

    db_session.refresh(session)

    assert session.status == "running"
    assert session.finished_at is None


@pytest.mark.parametrize(
    "session_type",
    ["questions", "mock_exam"],
)
def test_finish_question_session_with_null_correct(
    authenticated_client,
    db_session,
    test_user,
    session_type,
):
    """
    Permite finalizar sessões de questões ou simulados
    com correção explicitamente pendente.
    """

    session = Session(
        user_id=test_user.id,
        session_type=session_type,
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
            "questions_total": 100,
            "questions_correct": None,
        },
    )

    assert response.status_code == 200

    db_session.refresh(session)

    assert session.status == "finished"
    assert session.questions_total == 100
    assert session.questions_correct is None


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


def test_finish_questions_session_with_total(
    authenticated_client,
    db_session,
    test_user,
):
    """
    Deve finalizar sessão de questões quando
    questions_total for informado corretamente.
    """

    session = Session(
        user_id=test_user.id,
        session_type="questions",
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
            "questions_total": 100,
        },
    )

    assert response.status_code == 200

    db_session.refresh(session)

    assert session.status == "finished"
    assert session.questions_total == 100
    assert session.questions_correct is None


def test_finish_mock_exam_with_total_and_correct(
    authenticated_client,
    db_session,
    test_user,
):
    """
    Deve finalizar simulado com total de questões
    e quantidade de acertos.
    """

    session = Session(
        user_id=test_user.id,
        session_type="mock_exam",
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
            "questions_total": 100,
            "questions_correct": 72,
        },
    )

    assert response.status_code == 200

    db_session.refresh(session)

    assert session.status == "finished"
    assert session.questions_total == 100
    assert session.questions_correct == 72


def test_finish_question_session_without_total(
    authenticated_client,
    db_session,
    test_user,
):
    """
    Não deve finalizar sessão de questões sem
    questions_total.
    """

    session = Session(
        user_id=test_user.id,
        session_type="questions",
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

    assert response.status_code == 400

    db_session.refresh(session)

    assert session.status == "running"


def test_finish_question_session_with_null_total(
    authenticated_client,
    db_session,
    test_user,
):
    """
    Não deve finalizar sessão de questões com
    questions_total nulo.
    """

    session = Session(
        user_id=test_user.id,
        session_type="questions",
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
            "questions_total": None,
        },
    )

    assert response.status_code == 400

    db_session.refresh(session)

    assert session.status == "running"


def test_finish_question_session_with_zero_total(
    authenticated_client,
    db_session,
    test_user,
):
    """
    Não deve aceitar questions_total igual a zero.
    """

    session = Session(
        user_id=test_user.id,
        session_type="questions",
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
            "questions_total": 0,
        },
    )

    assert response.status_code == 400

    db_session.refresh(session)

    assert session.status == "running"


def test_finish_question_session_with_correct_greater_than_total(
    authenticated_client,
    db_session,
    test_user,
):
    """
    Não deve aceitar questions_correct maior que
    questions_total.
    """

    session = Session(
        user_id=test_user.id,
        session_type="questions",
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
            "questions_total": 50,
            "questions_correct": 51,
        },
    )

    assert response.status_code == 400

    db_session.refresh(session)

    assert session.status == "running"


def test_finish_question_session_with_zero_correct(
    authenticated_client,
    db_session,
    test_user,
):
    """
    Zero acertos é um resultado válido e diferente
    de correção pendente.
    """

    session = Session(
        user_id=test_user.id,
        session_type="questions",
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
            "questions_total": 50,
            "questions_correct": 0,
        },
    )

    assert response.status_code == 200

    db_session.refresh(session)

    assert session.questions_total == 50
    assert session.questions_correct == 0