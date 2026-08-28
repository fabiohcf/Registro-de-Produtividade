# app/routes/api_sessions.py

from flask import Blueprint, request, jsonify
from decimal import Decimal
from datetime import datetime, timezone
from app.models.session import Session
from app.database import SessionLocal
from app.utils.logging_utils import log_action
from app.models.goal import Goal
from app.models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.routes.session_service import (
    VALID_SESSION_TYPES,
    ACTIVE_SESSION_STATUSES,
    QUESTION_SESSION_TYPES,
    get_request_data,
    validate_positive_int,
    validate_session_type,
    get_session,
    get_active_session,
    calculate_duration_hours,
    serialize_session,
    validate_session_status,
    validate_finishable_session
)
import os


bp_sessions = Blueprint("bp_sessions", __name__, url_prefix="/api/sessions")

# Cria diretório de logs se não existir
os.makedirs("logs", exist_ok=True)


@bp_sessions.route("/start", methods=["POST"])
def start_session():
    data, error = get_request_data()
    if error:
        return error

    user_id = data.get("user_id")
    session_type = data.get("session_type")
    description = data.get("description")

    err = validate_positive_int(user_id, "ID do usuário")
    if err:
        return err

    err = validate_session_type(session_type)
    if err:
        return err

    if description:
        description = description.strip()

    now = datetime.now(timezone.utc)

    with SessionLocal() as db:

        user = db.get(User, user_id)
        if not user:
            return jsonify({"error": "Usuário não encontrado"}), 404

        active_session = get_active_session(db, user_id)

        if active_session:
            return jsonify(
                {"error": "Usuário já possui uma sessão ativa"}
            ), 400


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

        log_action(
            new_session.user_id,
            new_session.id,
            "start",
        )

        return jsonify(
            {
                "message": "Sessão iniciada com sucesso",
                "session": serialize_session(new_session),
            }
        ), 201


@bp_sessions.route("/pause", methods=["POST"])
def pause_session():

    data, error = get_request_data()
    if error:
        return error

    session_id = data.get("session_id")

    err = validate_positive_int(session_id, "ID da sessão")
    if err:
        return err

    with SessionLocal() as db:

        session_obj, err = get_session(db, session_id)
        if err:
            return err

        err = validate_session_status(session_obj, "running")
        if err:
            return err

        session_obj.status = "paused"
        session_obj.paused_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(session_obj)

        log_action(
            session_obj.user_id,
            session_obj.id,
            "pause",
        )

        return jsonify(
            {
                "message": "Sessão pausada com sucesso",
                "session": serialize_session(session_obj),
            }
        ), 200

@bp_sessions.route("/resume", methods=["POST"])
def resume_session():
    data, error = get_request_data()
    if error:
        return error

    session_id = data.get("session_id")

    err = validate_positive_int(session_id, "ID da sessão")
    if err:
        return err

    with SessionLocal() as db:

        session_obj, error = get_session(db, session_id)
        if error:
            return error

        err = validate_session_status(session_obj, "paused")
        if err:
            return err

        now = datetime.now(timezone.utc)

        paused_seconds = int(
            (now - session_obj.paused_at).total_seconds()
        )

        session_obj.paused_seconds += paused_seconds
        session_obj.paused_at = None
        session_obj.status = "running"

        db.commit()
        db.refresh(session_obj)

        log_action(
            session_obj.user_id,
            session_obj.id,
            "resume",
        )

        return (
            jsonify(
                {
                    "message": "Sessão retomada com sucesso.",
                    "session": serialize_session(session_obj),
                }
            ),
            200,
        )


@bp_sessions.route("/finish", methods=["POST"])
def finish_session():
    data, error = get_request_data()
    if error:
        return error

    session_id = data.get("session_id")

    err = validate_positive_int(
        session_id,
        "ID da sessão",
    )
    if err:
        return err

    now = datetime.now(timezone.utc)

    with SessionLocal() as db:

        session_obj, error = get_session(
            db,
            session_id,
        )
        if error:
            return error

        err = validate_finishable_session(session_obj)
        if err:
            return err

        # Caso esteja pausada,
        # soma o último período pausado.
        if session_obj.status == "paused":

            session_obj.paused_seconds += int(
                (now - session_obj.paused_at).total_seconds()
            )

            session_obj.paused_at = None

        session_obj.finished_at = now

        session_obj.status = "finished"

        session_obj.duration_hours = (
            calculate_duration_hours(
                session_obj.started_at,
                now,
                session_obj.paused_seconds,
            )
        )

        db.commit()
        db.refresh(session_obj)

        log_action(
            session_obj.user_id,
            session_obj.id,
            "finish",
        )

        return (
            jsonify(
                {
                    "message": "Sessão finalizada com sucesso.",
                    "session": serialize_session(session_obj),
                }
            ),
            200,
        )


@bp_sessions.route("/cancel", methods=["POST"])
def cancel_session():
    data, error = get_request_data()
    if error:
        return error

    session_id = data.get("session_id")

    err = validate_positive_int(
        session_id,
        "ID da sessão",
    )
    if err:
        return err

    with SessionLocal() as db:

        session_obj, error = get_session(
            db,
            session_id,
        )
        if error:
            return error

        if session_obj.status == "finished":
            return (
                jsonify(
                    {
                        "error": (
                            "Sessões finalizadas não podem ser canceladas."
                        )
                    }
                ),
                400,
            )

        user_id = session_obj.user_id

        log_action(
            user_id,
            session_obj.id,
            "cancel",
        )

        db.delete(session_obj)
        db.commit()

        return (
            jsonify(
                {
                    "message": "Sessão cancelada com sucesso."
                }
            ),
            200,
        )



@bp_sessions.route("/list", methods=["GET"])
@jwt_required()
def list_sessions():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return jsonify({"error": "Identidade de usuário inválida"}), 401

    with SessionLocal() as db:
        query = db.query(Session).filter(
            Session.user_id == user_id
        )

        if start_date:
            query = query.filter(
                Session.started_at >= start_date
            )

        if end_date:
            query = query.filter(
                Session.started_at <= end_date
            )

        sessions = query.all()

        return jsonify(
            [serialize_session(session) for session in sessions]
        ), 200