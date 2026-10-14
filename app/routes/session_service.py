# app/routes/session_service.py

from datetime import datetime, timezone
from decimal import Decimal

from flask_sqlalchemy import session

from app.models.session import Session


# ==========================================================
# Session V2 constants
# ==========================================================

VALID_SESSION_TYPES = {
    "study",
    "revision",
    "questions",
    "essay",
    "mock_exam",
}

ACTIVE_SESSION_STATUSES = {
    "running",
    "paused",
}

QUESTION_SESSION_TYPES = {
    "questions",
    "mock_exam",
}


# ==========================================================
# Validations
# ==========================================================

def validate_positive_int(value):
    """
    Valida se o valor é um inteiro positivo.
    """

    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value <= 0
    ):
        raise ValueError(
            "O valor deve ser um número inteiro positivo"
        )

def validate_session_type(session_type):
    """
    Valida o tipo da sessão.
    """

    if session_type not in VALID_SESSION_TYPES:
        raise ValueError(
            f"Tipo de sessão inválido. "
            f"Valores aceitos: {sorted(VALID_SESSION_TYPES)}"
        )


# ==========================================================
# Database helpers
# ==========================================================

def get_session(db, session_id):
    """
    Busca uma sessão pelo ID.
    """

    return db.get(Session, session_id)


def get_user_session(db, session_id, user_id):
    """
    Busca uma sessão garantindo que ela pertence ao usuário.
    """

    session = db.get(Session, session_id)

    if session is None:
        return None

    if session.user_id != user_id:
        return None

    return session


def get_active_session(db, user_id):
    """
    Retorna a sessão ativa do usuário.
    """

    return (
        db.query(Session)
        .filter(
            Session.user_id == user_id,
            Session.status.in_(ACTIVE_SESSION_STATUSES),
        )
        .first()
    )


# ==========================================================
# Business validations
# ==========================================================

def validate_session_status(session_obj, expected_status):
    """
    Verifica se a sessão está no status esperado.
    """

    if session_obj.status != expected_status:
        raise ValueError(
            f"A sessão deve estar em '{expected_status}'."
        )


def validate_finishable_session(session):
    """
    Valida se a sessão pode ser finalizada.

    Apenas sessões em execução ou pausadas
    podem ser finalizadas.
    """

    if session.status not in ACTIVE_SESSION_STATUSES:
        raise ValueError(
            "Somente sessões em execução ou pausadas "
            "podem ser finalizadas."
        )


def validate_question_results(
    questions_total,
    questions_correct,
):
    """
    Valida os resultados de sessões de questões
    e simulados.

    QT deve ser inteiro positivo.
    QC pode ser None ou inteiro entre zero e QT.
    """

    validate_positive_int(questions_total)

    if questions_correct is not None:
        if (
            isinstance(questions_correct, bool)
            or not isinstance(questions_correct, int)
            or questions_correct < 0
        ):
            raise ValueError(
                "questions_correct deve ser um número "
                "inteiro não negativo"
            )

        if questions_correct > questions_total:
            raise ValueError(
                "questions_correct não pode ser maior "
                "que questions_total"
            )

# ==========================================================
# Session operations
# ==========================================================

def start_session(
    db,
    user_id,
    session_type,
    description=None,
):
    """
    Inicia uma nova sessão para o usuário.
    """

    validate_positive_int(user_id)
    validate_session_type(session_type)

    active_session = get_active_session(db, user_id)

    if active_session:
        raise ValueError(
            "Usuário já possui uma sessão ativa"
        )

    if description:
        description = description.strip()

    now = utc_now()

    new_session = Session(
        user_id=user_id,
        session_type=session_type,
        description=description,
        status="running",
        started_at=now,
        finished_at=None,
        duration_hours=Decimal("0"),
        paused_seconds=0,
        paused_at=None,
        questions_total=None,
        questions_correct=None,
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return new_session


def pause_session(db, session_id, user_id):
    """
    Pausa uma sessão em execução.
    """

    validate_positive_int(session_id)

    session = get_user_session(
        db,
        session_id,
        user_id,
    )

    if session is None:
        return None

    validate_session_status(
        session,
        "running",
    )

    session.status = "paused"
    session.paused_at = utc_now()

    db.commit()
    db.refresh(session)

    return session


def resume_session(db, session_id, user_id):
    """
    Retoma uma sessão pausada.
    """

    validate_positive_int(session_id)

    session = get_user_session(
        db,
        session_id,
        user_id,
    )

    if session is None:
        return None

    validate_session_status(
        session,
        "paused",
    )

    now = utc_now()

    paused_at = ensure_utc(session.paused_at)

    paused_seconds = int(
        (now - paused_at).total_seconds()
    )

    session.paused_seconds += paused_seconds
    session.paused_at = None
    session.status = "running"

    db.commit()
    db.refresh(session)

    return session


def finish_session(
    db,
    session_id,
    user_id,
    questions_total=None,
    questions_correct=None,
    questions_total_provided=False,
    questions_correct_provided=False,
):
    """
    Finaliza uma sessão em execução ou pausada.

    Sessões de questões e simulados exigem
    questions_total. questions_correct é opcional.
    """

    validate_positive_int(session_id)

    session = get_user_session(
        db,
        session_id,
        user_id,
    )

    if session is None:
        return None

    validate_finishable_session(session)

    if session.session_type not in QUESTION_SESSION_TYPES:
        if (
            questions_total_provided
            or questions_correct_provided
        ):
            raise ValueError(
                "Campos de questões são permitidos apenas "
                "para sessões de questões ou simulados"
            )

    else:
        validate_positive_int(questions_total)

        if questions_correct is not None:
            if (
                isinstance(questions_correct, bool)
                or not isinstance(questions_correct, int)
                or questions_correct < 0
            ):
                raise ValueError(
                    "questions_correct deve ser um número "
                    "inteiro não negativo"
                )

            if questions_correct > questions_total:
                raise ValueError(
                    "questions_correct não pode ser maior "
                    "que questions_total"
                )

        session.questions_total = questions_total
        session.questions_correct = questions_correct

    now = utc_now()

    # Caso esteja pausada, soma o último período pausado.
    if session.status == "paused":
        paused_at = ensure_utc(session.paused_at)

        session.paused_seconds += int(
            (now - paused_at).total_seconds()
        )

        session.paused_at = None

    session.finished_at = now
    session.status = "finished"

    session.duration_hours = calculate_duration_hours(
        ensure_utc(session.started_at),
        now,
        session.paused_seconds,
    )

    db.commit()
    db.refresh(session)

    return session


def update_session_results(
    db,
    session_id,
    user_id,
    questions_total=None,
    questions_correct=None,
    questions_total_provided=False,
    questions_correct_provided=False,
):
    """
    Atualiza os resultados de uma sessão finalizada.

    Campos omitidos preservam os valores existentes.
    QC pode ser None para indicar correção pendente.
    """

    validate_positive_int(session_id)

    session = get_user_session(
        db,
        session_id,
        user_id,
    )

    if session is None:
        return None

    if session.status != "finished":
        raise ValueError(
            "Somente sessões finalizadas podem ter "
            "seus resultados editados."
        )

    if session.session_type not in QUESTION_SESSION_TYPES:
        raise ValueError(
            "Somente sessões de questões ou simulados "
            "podem ter seus resultados editados."
        )

    new_total = (
        questions_total
        if questions_total_provided
        else session.questions_total
    )

    new_correct = (
        questions_correct
        if questions_correct_provided
        else session.questions_correct
    )

    validate_question_results(
        new_total,
        new_correct,
    )

    session.questions_total = new_total
    session.questions_correct = new_correct

    db.commit()
    db.refresh(session)

    return session


def cancel_session(db, session_id, user_id):
    """
    Cancela uma sessão ativa.

    A sessão é removida fisicamente do banco.
    """

    validate_positive_int(session_id)

    session = get_user_session(
        db,
        session_id,
        user_id,
    )

    if session is None:
        return None

    if session.status == "finished":
        raise ValueError(
            "Sessões finalizadas não podem ser canceladas."
        )

    session_user_id = session.user_id
    session_id = session.id

    db.delete(session)
    db.commit()

    return {
        "user_id": session_user_id,
        "session_id": session_id,
    }

def list_sessions(db, user_id):
    """
    Lista todas as sessões pertencentes ao usuário autenticado.
    """

    validate_positive_int(user_id)

    return (
        db.query(Session)
        .filter(Session.user_id == user_id)
        .all()
    )


# ==========================================================
# Time helpers
# ==========================================================


def ensure_utc(value):
    """
    Normaliza um datetime para UTC.

    SQLite pode devolver valores DateTime sem informação
    de timezone, mesmo quando a coluna usa timezone=True.
    Datetimes naive do domínio são tratados como UTC.
    """

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)

def utc_now():
    """
    Retorna o instante atual em UTC.

    Centralizar a obtenção do horário permite testes
    determinísticos das operações temporais da sessão.
    """

    return datetime.now(timezone.utc)


def calculate_duration_hours(
    started_at,
    finished_at,
    paused_seconds,
):
    """
    Calcula o tempo líquido da sessão.
    """

    started_at = ensure_utc(started_at)
    finished_at = ensure_utc(finished_at)


    elapsed_seconds = (
        finished_at - started_at
    ).total_seconds()

    active_seconds = (
        elapsed_seconds - (paused_seconds or 0)
    )

    if active_seconds < 0:
        active_seconds = 0

    return Decimal(str(active_seconds)) / Decimal("3600")