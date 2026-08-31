# app/routes/session_service.py

from decimal import Decimal

from flask import jsonify, request

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
# Generic validations
# ==========================================================

def get_request_data():
    """
    Obtém e valida o JSON da requisição.
    """

    data = request.get_json()

    if not data:
        return None, (
            jsonify({"error": "Dados JSON são obrigatórios"}),
            400,
        )

    return data, None


def validate_positive_int(value, field_name):
    """
    Valida inteiro positivo.
    """

    if not isinstance(value, int) or value <= 0:
        return (
            jsonify(
                {
                    "error": f"{field_name} deve ser um número inteiro positivo"
                }
            ),
            400,
        )

    return None


def validate_session_type(session_type):
    """
    Valida o tipo da sessão.
    """

    if session_type not in VALID_SESSION_TYPES:
        return (
            jsonify(
                {
                    "error": (
                        f"Tipo de sessão inválido. "
                        f"Valores aceitos: {sorted(VALID_SESSION_TYPES)}"
                    )
                }
            ),
            400,
        )

    return None


# ==========================================================
# Database helpers
# ==========================================================

def get_session(db, session_id):
    """
    Busca sessão pelo ID.
    """

    session = db.get(Session, session_id)

    if session is None:
        return None, (
            jsonify({"error": "Sessão não encontrada"}),
            404,
        )

    return session, None


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
        return (
            jsonify(
                {
                    "error": (
                        f"A sessão deve estar em "
                        f"'{expected_status}'."
                    )
                }
            ),
            400,
        )

    return None

def validate_finishable_session(session):
    """
    Valida se a sessão pode ser finalizada.

    Apenas sessões em execução ou pausadas
    podem ser finalizadas.
    """

    if session.status not in {"running", "paused"}:
        return (
            jsonify(
                {
                    "error": (
                        "Somente sessões em execução "
                        "ou pausadas podem ser finalizadas."
                    )
                }
            ),
            400,
        )

    return None

# ==========================================================
# Time helpers
# ==========================================================

def calculate_duration_hours(
    started_at,
    finished_at,
    paused_seconds,
):
    """
    Calcula o tempo líquido da sessão.
    """

    elapsed_seconds = (
        finished_at - started_at
    ).total_seconds()

    active_seconds = elapsed_seconds - (paused_seconds or 0)

    if active_seconds < 0:
        active_seconds = 0

    return Decimal(active_seconds / 3600)


# ==========================================================
# Serialization
# ==========================================================

def serialize_session(session):
    """
    Converte Session em dicionário JSON.
    """

    return {
        "id": session.id,
        "user_id": session.user_id,

        "status": session.status,

        "session_type": session.session_type,
        "description": session.description,

        "started_at": (
            session.started_at.isoformat()
            if session.started_at
            else None
        ),

        "finished_at": (
            session.finished_at.isoformat()
            if session.finished_at
            else None
        ),

        "duration_hours": (
            float(session.duration_hours)
            if session.duration_hours is not None
            else 0
        ),

        "paused_seconds": session.paused_seconds,

        "questions_total": session.questions_total,
        "questions_correct": session.questions_correct,
    }