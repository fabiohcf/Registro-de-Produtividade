# tests/test_sessions_api/test_sessions_api_patch.py

from datetime import datetime, timezone
from decimal import Decimal

from app.models.session import Session

import pytest


@pytest.mark.parametrize(
    "invalid_total",
    [
        0,
        -1,
        2.5,
        "50",
        True,
        False,
    ],
)
def test_patch_rejects_invalid_total(
    authenticated_client,
    db_session,
    test_user,
    invalid_total,
):
    """
    Rejeita valores inválidos de QT e preserva
    os resultados anteriormente armazenados.
    """

    session = Session(
        user_id=test_user.id,
        session_type="questions",
        status="finished",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration_hours=Decimal("1"),
        paused_seconds=0,
        questions_total=50,
        questions_correct=30,
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.patch(
        f"/api/sessions/{session.id}",
        json={
            "questions_total": invalid_total,
        },
    )

    assert response.status_code == 400

    db_session.refresh(session)

    assert session.questions_total == 50
    assert session.questions_correct == 30
    assert session.status == "finished"



@pytest.mark.parametrize(
    "invalid_correct",
    [
        -1,
        2.5,
        "30",
        True,
        False,
        51,
    ],
)
def test_patch_rejects_invalid_correct(
    authenticated_client,
    db_session,
    test_user,
    invalid_correct,
):
    """
    Rejeita valores inválidos de QC e preserva
    os resultados anteriormente armazenados.
    """

    session = Session(
        user_id=test_user.id,
        session_type="questions",
        status="finished",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration_hours=Decimal("1"),
        paused_seconds=0,
        questions_total=50,
        questions_correct=30,
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.patch(
        f"/api/sessions/{session.id}",
        json={
            "questions_correct": invalid_correct,
        },
    )

    assert response.status_code == 400

    db_session.refresh(session)

    assert session.questions_total == 50
    assert session.questions_correct == 30
    assert session.status == "finished"


@pytest.mark.parametrize(
    "status",
    [
        "running",
        "paused",
    ],
)
def test_patch_rejects_active_sessions(
    authenticated_client,
    db_session,
    test_user,
    status,
):
    """
    Impede a edição de resultados de sessões
    que ainda não foram finalizadas.
    """

    started_at = datetime.now(timezone.utc)

    session = Session(
        user_id=test_user.id,
        session_type="questions",
        status=status,
        started_at=started_at,
        paused_at=(
            started_at if status == "paused" else None
        ),
        finished_at=None,
        duration_hours=Decimal("0"),
        paused_seconds=0,
        questions_total=50,
        questions_correct=30,
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.patch(
        f"/api/sessions/{session.id}",
        json={
            "questions_correct": 40,
        },
    )

    assert response.status_code == 400

    db_session.refresh(session)

    assert session.questions_total == 50
    assert session.questions_correct == 30
    assert session.status == status


@pytest.mark.parametrize(
    "session_type",
    [
        "study",
        "revision",
        "essay",
    ],
)
def test_patch_rejects_non_question_session_types(
    authenticated_client,
    db_session,
    test_user,
    session_type,
):
    """
    Impede a edição de resultados em sessões
    que não são de questões ou simulados.
    """

    session = Session(
        user_id=test_user.id,
        session_type=session_type,
        status="finished",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration_hours=Decimal("1"),
        paused_seconds=0,
        questions_total=None,
        questions_correct=None,
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.patch(
        f"/api/sessions/{session.id}",
        json={
            "questions_total": 50,
            "questions_correct": 30,
        },
    )

    assert response.status_code == 400

    db_session.refresh(session)

    assert session.questions_total is None
    assert session.questions_correct is None
    assert session.status == "finished"
    assert session.session_type == session_type


@pytest.mark.parametrize(
    "invalid_field, value",
    [
        ("status", "running"),
        ("session_type", "study"),
        ("duration_hours", 10),
        ("user_id", 999),
        ("description", "Descrição alterada"),
        ("finished_at", None),
    ],
)
def test_patch_rejects_unknown_fields(
    authenticated_client,
    db_session,
    test_user,
    invalid_field,
    value,
):
    """
    Rejeita campos não permitidos no PATCH
    e preserva os dados da sessão.
    """

    session = Session(
        user_id=test_user.id,
        session_type="questions",
        status="finished",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration_hours=Decimal("1"),
        paused_seconds=0,
        questions_total=50,
        questions_correct=30,
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.patch(
        f"/api/sessions/{session.id}",
        json={
            invalid_field: value,
            "questions_correct": 40,
        },
    )

    assert response.status_code == 400

    db_session.refresh(session)

    assert session.questions_total == 50
    assert session.questions_correct == 30
    assert session.status == "finished"
    assert session.session_type == "questions"
    assert session.user_id == test_user.id
    assert session.duration_hours == Decimal("1")


@pytest.mark.parametrize(
    "payload",
    [
        {},
        [],
        [1, 2],
        "invalid",
        123,
        None,
    ],
)
def test_patch_rejects_invalid_payload(
    authenticated_client,
    db_session,
    test_user,
    payload,
):
    """
    Rejeita payloads vazios ou que não sejam
    objetos JSON válidos.
    """

    session = Session(
        user_id=test_user.id,
        session_type="questions",
        status="finished",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration_hours=Decimal("1"),
        paused_seconds=0,
        questions_total=50,
        questions_correct=30,
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.patch(
        f"/api/sessions/{session.id}",
        json=payload,
    )

    assert response.status_code == 400

    db_session.refresh(session)

    assert session.questions_total == 50
    assert session.questions_correct == 30
    assert session.status == "finished"



@pytest.mark.parametrize(
    "session_type",
    [
        "questions",
        "mock_exam",
    ],
)
def test_patch_allows_zero_correct_for_question_session_types(
    authenticated_client,
    db_session,
    test_user,
    session_type,
):
    """
    Permite QC igual a zero em sessões finalizadas
    de questões e simulados.
    """

    session = Session(
        user_id=test_user.id,
        session_type=session_type,
        status="finished",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration_hours=Decimal("1"),
        paused_seconds=0,
        questions_total=50,
        questions_correct=30,
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.patch(
        f"/api/sessions/{session.id}",
        json={
            "questions_correct": 0,
        },
    )

    assert response.status_code == 200

    db_session.refresh(session)

    assert session.questions_total == 50
    assert session.questions_correct == 0
    assert session.status == "finished"
    assert session.session_type == session_type


def test_patch_updates_correct_without_changing_total(
    authenticated_client,
    db_session,
    test_user,
):
    """
    Deve atualizar apenas questions_correct de uma
    sessão finalizada, preservando questions_total.
    """

    session = Session(
        user_id=test_user.id,
        session_type="questions",
        status="finished",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration_hours=Decimal("1"),
        paused_seconds=0,
        questions_total=50,
        questions_correct=30,
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.patch(
        f"/api/sessions/{session.id}",
        json={
            "questions_correct": 40,
        },
    )

    assert response.status_code == 200

    db_session.refresh(session)

    assert session.questions_total == 50
    assert session.questions_correct == 40
    assert session.status == "finished"


def test_patch_updates_total_without_changing_correct(
    authenticated_client,
    db_session,
    test_user,
):
    """
    Deve atualizar apenas questions_total,
    preservando questions_correct.
    """

    session = Session(
        user_id=test_user.id,
        session_type="questions",
        status="finished",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration_hours=Decimal("1"),
        paused_seconds=0,
        questions_total=50,
        questions_correct=30,
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.patch(
        f"/api/sessions/{session.id}",
        json={
            "questions_total": 60,
        },
    )

    assert response.status_code == 200

    db_session.refresh(session)

    assert session.questions_total == 60
    assert session.questions_correct == 30
    assert session.status == "finished"


def test_patch_rejects_total_lower_than_existing_correct(
    authenticated_client,
    db_session,
    test_user,
):
    """
    Rejeita a redução de QT abaixo do QC armazenado,
    preservando os valores originais.
    """

    session = Session(
        user_id=test_user.id,
        session_type="questions",
        status="finished",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration_hours=Decimal("1"),
        paused_seconds=0,
        questions_total=50,
        questions_correct=30,
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.patch(
        f"/api/sessions/{session.id}",
        json={
            "questions_total": 20,
        },
    )

    assert response.status_code == 400

    db_session.refresh(session)

    assert session.questions_total == 50
    assert session.questions_correct == 30
    assert session.status == "finished"




def test_patch_allows_null_correct_for_pending_review(
    authenticated_client,
    db_session,
    test_user,
):
    """
    Permite limpar QC para indicar correção pendente,
    preservando o total de questões.
    """

    session = Session(
        user_id=test_user.id,
        session_type="questions",
        status="finished",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration_hours=Decimal("1"),
        paused_seconds=0,
        questions_total=50,
        questions_correct=30,
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.patch(
        f"/api/sessions/{session.id}",
        json={
            "questions_correct": None,
        },
    )

    assert response.status_code == 200

    db_session.refresh(session)

    assert session.questions_total == 50
    assert session.questions_correct is None
    assert session.status == "finished"



def test_patch_rejects_null_total(
    authenticated_client,
    db_session,
    test_user,
):
    """
    Rejeita QT nulo e preserva os resultados existentes.
    """

    session = Session(
        user_id=test_user.id,
        session_type="questions",
        status="finished",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration_hours=Decimal("1"),
        paused_seconds=0,
        questions_total=50,
        questions_correct=30,
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.patch(
        f"/api/sessions/{session.id}",
        json={
            "questions_total": None,
        },
    )

    assert response.status_code == 400

    db_session.refresh(session)

    assert session.questions_total == 50
    assert session.questions_correct == 30
    assert session.status == "finished"


def test_patch_requires_authentication(
    client,
    db_session,
    test_user,
):
    """
    Rejeita atualização de resultados sem autenticação JWT.
    """

    session = Session(
        user_id=test_user.id,
        session_type="questions",
        status="finished",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration_hours=Decimal("1"),
        paused_seconds=0,
        questions_total=50,
        questions_correct=30,
    )

    db_session.add(session)
    db_session.commit()

    response = client.patch(
        f"/api/sessions/{session.id}",
        json={
            "questions_correct": 40,
        },
    )

    assert response.status_code == 401

    db_session.refresh(session)

    assert session.questions_total == 50
    assert session.questions_correct == 30
    assert session.status == "finished"


def test_patch_rejects_session_from_another_user(
    authenticated_client,
    db_session,
    other_user,
):
    """
    Impede a alteração de sessões pertencentes
    a outro usuário, retornando HTTP 404.
    """

    session = Session(
        user_id=other_user.id,
        session_type="questions",
        status="finished",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        duration_hours=Decimal("1"),
        paused_seconds=0,
        questions_total=50,
        questions_correct=30,
    )

    db_session.add(session)
    db_session.commit()

    response = authenticated_client.patch(
        f"/api/sessions/{session.id}",
        json={
            "questions_correct": 40,
        },
    )

    assert response.status_code == 404

    db_session.refresh(session)

    assert session.questions_total == 50
    assert session.questions_correct == 30
    assert session.status == "finished"


def test_patch_returns_404_for_nonexistent_session(
    authenticated_client,
):
    """
    Retorna HTTP 404 quando a sessão solicitada
    não existe no banco de dados.
    """

    response = authenticated_client.patch(
        "/api/sessions/999999",
        json={
            "questions_correct": 40,
        },
    )

    assert response.status_code == 404

    assert response.get_json() == {
        "error": "Sessão não encontrada"
    }


def test_patch_preserves_session_time_fields(
    authenticated_client,
    db_session,
    test_user,
):
    """
    Preserva os dados temporais da sessão
    durante a atualização dos resultados.
    """

    started_at = datetime(
        2026, 10, 10, 14, 0, tzinfo=timezone.utc
    )
    finished_at = datetime(
        2026, 10, 10, 15, 30, tzinfo=timezone.utc
    )

    session = Session(
        user_id=test_user.id,
        session_type="questions",
        status="finished",
        started_at=started_at,
        finished_at=finished_at,
        duration_hours=Decimal("1.2500"),
        paused_seconds=900,
        questions_total=50,
        questions_correct=30,
    )

    db_session.add(session)
    db_session.commit()

    original_started_at = session.started_at
    original_finished_at = session.finished_at
    original_duration = session.duration_hours
    original_paused_seconds = session.paused_seconds

    response = authenticated_client.patch(
        f"/api/sessions/{session.id}",
        json={
            "questions_correct": 40,
        },
    )

    assert response.status_code == 200

    db_session.refresh(session)

    assert session.questions_total == 50
    assert session.questions_correct == 40

    assert session.started_at == original_started_at
    assert session.finished_at == original_finished_at
    assert session.duration_hours == original_duration
    assert session.paused_seconds == original_paused_seconds
    assert session.status == "finished"