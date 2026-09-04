from flask import Blueprint, request, jsonify

from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import SessionLocal
from app.utils.logging_utils import log_action
from app.routes.session_service import (
    start_session as start_session_service,
    pause_session as pause_session_service,
    resume_session as resume_session_service,
    finish_session as finish_session_service,
    cancel_session as cancel_session_service,
    list_sessions as list_sessions_service,
)

import os


bp_sessions = Blueprint(
    "bp_sessions",
    __name__,
    url_prefix="/api/sessions",
)

# Cria diretório de logs se não existir
os.makedirs("logs", exist_ok=True)


def _get_authenticated_user_id():
    """
    Obtém o ID do usuário autenticado a partir do JWT.

    A identidade do usuário nunca deve ser obtida
    do corpo da requisição.
    """

    try:
        return int(get_jwt_identity())
    except (TypeError, ValueError):
        return None


def _serialize_session(session):
    """
    Converte uma sessão SQLAlchemy para o formato
    de resposta da API.
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


# ==========================================================
# START
# ==========================================================

@bp_sessions.route("/start", methods=["POST"])
@jwt_required()
def start_session():
    data = request.get_json()

    if not data:
        return jsonify(
            {"error": "Dados JSON são obrigatórios"}
        ), 400

    user_id = _get_authenticated_user_id()

    if user_id is None:
        return jsonify(
            {"error": "Identidade de usuário inválida"}
        ), 401

    session_type = data.get("session_type")
    description = data.get("description")

    with SessionLocal() as db:
        try:
            session = start_session_service(
                db=db,
                user_id=user_id,
                session_type=session_type,
                description=description,
            )
        except ValueError as error:
            return jsonify(
                {"error": str(error)}
            ), 400

        log_action(
            session.user_id,
            session.id,
            "start",
        )

        return jsonify(
            {
                "message": "Sessão iniciada com sucesso",
                "session": _serialize_session(session),
            }
        ), 201


# ==========================================================
# PAUSE
# ==========================================================

@bp_sessions.route("/pause", methods=["POST"])
@jwt_required()
def pause_session():

    data = request.get_json()

    if not data:
        return jsonify(
            {"error": "Dados JSON são obrigatórios"}
        ), 400

    user_id = _get_authenticated_user_id()

    if user_id is None:
        return jsonify(
            {"error": "Identidade de usuário inválida"}
        ), 401

    session_id = data.get("session_id")

    with SessionLocal() as db:
        try:
            session = pause_session_service(
                db=db,
                session_id=session_id,
                user_id=user_id,
            )
        except ValueError as error:
            return jsonify(
                {"error": str(error)}
            ), 400

        if session is None:
            return jsonify(
                {"error": "Sessão não encontrada"}
            ), 404

        log_action(
            session.user_id,
            session.id,
            "pause",
        )

        return jsonify(
            {
                "message": "Sessão pausada com sucesso",
                "session": _serialize_session(session),
            }
        ), 200


# ==========================================================
# RESUME
# ==========================================================

@bp_sessions.route("/resume", methods=["POST"])
@jwt_required()
def resume_session():

    data = request.get_json()

    if not data:
        return jsonify(
            {"error": "Dados JSON são obrigatórios"}
        ), 400

    user_id = _get_authenticated_user_id()

    if user_id is None:
        return jsonify(
            {"error": "Identidade de usuário inválida"}
        ), 401

    session_id = data.get("session_id")

    with SessionLocal() as db:
        try:
            session = resume_session_service(
                db=db,
                session_id=session_id,
                user_id=user_id,
            )
        except ValueError as error:
            return jsonify(
                {"error": str(error)}
            ), 400

        if session is None:
            return jsonify(
                {"error": "Sessão não encontrada"}
            ), 404

        log_action(
            session.user_id,
            session.id,
            "resume",
        )

        return (
            jsonify(
                {
                    "message": "Sessão retomada com sucesso.",
                    "session": _serialize_session(session),
                }
            ),
            200,
        )


# ==========================================================
# FINISH
# ==========================================================

@bp_sessions.route("/finish", methods=["POST"])
@jwt_required()
def finish_session():

    data = request.get_json()

    if not data:
        return jsonify(
            {"error": "Dados JSON são obrigatórios"}
        ), 400

    user_id = _get_authenticated_user_id()

    if user_id is None:
        return jsonify(
            {"error": "Identidade de usuário inválida"}
        ), 401

    session_id = data.get("session_id")

    with SessionLocal() as db:
        try:
            session = finish_session_service(
                db=db,
                session_id=session_id,
                user_id=user_id,
            )
        except ValueError as error:
            return jsonify(
                {"error": str(error)}
            ), 400

        if session is None:
            return jsonify(
                {"error": "Sessão não encontrada"}
            ), 404

        log_action(
            session.user_id,
            session.id,
            "finish",
        )

        return (
            jsonify(
                {
                    "message": "Sessão finalizada com sucesso.",
                    "session": _serialize_session(session),
                }
            ),
            200,
        )


# ==========================================================
# CANCEL
# ==========================================================

@bp_sessions.route("/cancel", methods=["POST"])
@jwt_required()
def cancel_session():

    data = request.get_json()

    if not data:
        return jsonify(
            {"error": "Dados JSON são obrigatórios"}
        ), 400

    user_id = _get_authenticated_user_id()

    if user_id is None:
        return jsonify(
            {"error": "Identidade de usuário inválida"}
        ), 401

    session_id = data.get("session_id")

    if session_id is None:
        return jsonify(
            {"error": "ID da sessão é obrigatório"}
        ), 400

    with SessionLocal() as db:
        try:
            result = cancel_session_service(
                db=db,
                session_id=session_id,
                user_id=user_id,
            )
        except ValueError as error:
            return jsonify(
                {"error": str(error)}
            ), 400

        if result is None:
            return jsonify(
                {"error": "Sessão não encontrada"}
            ), 404

        log_action(
            result["user_id"],
            result["session_id"],
            "cancel",
        )

        return jsonify(
            {
                "message": "Sessão cancelada com sucesso."
            }
        ), 200


# ==========================================================
# LIST
# ==========================================================

@bp_sessions.route("/list", methods=["GET"])
@jwt_required()
def list_sessions():

    user_id = _get_authenticated_user_id()

    if user_id is None:
        return jsonify(
            {"error": "Identidade de usuário inválida"}
        ), 401

    with SessionLocal() as db:
        try:
            sessions = list_sessions_service(
                db=db,
                user_id=user_id,
            )
        except ValueError as error:
            return jsonify(
                {"error": str(error)}
            ), 400

        return jsonify(
            [
                _serialize_session(session)
                for session in sessions
            ]
        ), 200