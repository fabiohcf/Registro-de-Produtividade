# tests/test_validations.py

import uuid
import pytest
from werkzeug.security import generate_password_hash
from app.models.user import User
from tests.conftest import client


def test_create_user_with_invalid_email(client, db_session):
    """Testa criação de usuário com email inválido."""
    resp = client.post(
        "/api/users/",
        json={"username": "TestUser", "email": "email-invalido", "password": "123456"},
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert "Dados inválidos" in data["error"]
    assert "Email deve ter formato válido" in data["details"]


def test_create_user_with_short_password(client, db_session):
    """Testa criação de usuário com senha muito curta."""
    resp = client.post(
        "/api/users/",
        json={
            "username": "TestUser",
            "email": f"{uuid.uuid4()}@example.com",
            "password": "123",
        },
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert "Senha deve ter pelo menos 6 caracteres" in data["details"]


def test_create_user_with_duplicate_email(client, db_session):
    """Testa criação de usuário com email duplicado."""
    email = f"{uuid.uuid4()}@example.com"

    # Primeira criação
    resp1 = client.post(
        "/api/users/",
        json={"username": "User1", "email": email, "password": "123456"},
    )
    assert resp1.status_code == 201

    # Segunda criação com mesmo email
    resp2 = client.post(
        "/api/users/",
        json={"username": "User2", "email": email, "password": "123456"},
    )
    assert resp2.status_code == 400
    data = resp2.get_json()
    assert data["error"] == "Email já está em uso"


def test_update_user_with_invalid_email(client, db_session):
    """Testa atualização de usuário com email inválido."""
    # Criar usuário
    user = User(
        username="TestUser",
        email=f"{uuid.uuid4()}@example.com",
        password_hash=generate_password_hash("123456"),
    )
    db_session.add(user)
    db_session.commit()

    resp = client.put(f"/api/users/{user.id}", json={"email": "email-invalido"})
    assert resp.status_code == 400
    data = resp.get_json()
    assert "Email deve ter formato válido" in data["details"]


def test_create_goal_with_invalid_user_id(client, db_session):
    """Testa criação de meta com usuário inexistente."""
    resp = client.post(
        "/api/goals/",
        json={
            "description": "Estudar Python",
            "category": "Estudo",
            "target_hours": 10,
            "user_id": 99999,  # ID inexistente
        },
    )
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["error"] == "Usuário não encontrado"




def test_sessions_without_json_data(authenticated_client):
    """Testa endpoint de sessão sem dados JSON."""

    resp = authenticated_client.post(
        "/api/sessions/start",
        data="não é json",
        content_type="text/plain",
    )

    # Flask retorna 415 para content-type não suportado.
    assert resp.status_code == 415



def test_goals_without_json_data(client, db_session):
    """Testa criação de meta sem dados JSON."""
    resp = client.post("/api/goals/", data="não é json", content_type="text/plain")
    # Flask retorna 415 para content-type não suportado
    assert resp.status_code == 415
