# app/routes/api_auth.py

from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    set_access_cookies,
    set_refresh_cookies,
    jwt_required
)
from app.models.user import User
from app.database import SessionLocal


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    with SessionLocal() as db:
        user = db.query(User).filter_by(
            username=username
        ).first()

        if not user or not check_password_hash(
            user.password_hash,
            password,
        ):
            return jsonify({"msg": "Credenciais inválidas"}), 401

        access_token = create_access_token(
            identity=str(user.id)
        )

        refresh_token = create_refresh_token(
            identity=str(user.id)
        )

        resp = jsonify({
            "msg": "Login bem-sucedido"
        })

        set_access_cookies(
            resp,
            access_token,
        )

        set_refresh_cookies(
            resp,
            refresh_token,
        )

        return resp, 200

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)

    resp = jsonify({"access_token": new_access_token})
    set_access_cookies(resp, new_access_token)

    return resp, 200
