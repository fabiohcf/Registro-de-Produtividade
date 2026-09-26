# app/routes/session_service.py

from datetime import datetime, timezone
from decimal import Decimal

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

    if not isinstance(value, int) or value <= 0:
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

    now = datetime.now(timezone.utc)

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
    session.paused_at = datetime.now(timezone.utc)

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

    now = datetime.now(timezone.utc)

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


def finish_session(db, session_id, user_id):
    """
    Finaliza uma sessão em execução ou pausada.
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

    now = datetime.now(timezone.utc)

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

    return Decimal(active_seconds / 3600)
