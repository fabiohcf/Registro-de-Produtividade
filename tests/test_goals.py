# tests/test_goals.py

import uuid

import pytest
from werkzeug.security import generate_password_hash

from app.models.user import User
from app.models.goal import Goal


# ==========================================================
# Fixtures
# ==========================================================



# ==========================================================
# CREATE GOAL
# ==========================================================

def test_create_weekly_goal_with_hours(client, db_session, test_user):
    """Deve criar meta semanal somente de horas."""

    response = client.post(
        "/api/goals/",
        json={
            "user_id": test_user.id,
            "target_hours": 10,
        },
    )

    print("STATUS:", response.status_code)
    print("BODY:", response.get_json())

    assert response.status_code == 201


def test_create_weekly_goal_with_questions(client, db_session, test_user):
    """Deve criar meta semanal somente de questões."""

    response = client.post(
        "/api/goals/",
        json={
            "user_id": test_user.id,
            "target_questions": 300,
        },
    )

    assert response.status_code == 201

    goal = db_session.query(Goal).filter_by(
        user_id=test_user.id
    ).first()

    assert goal is not None
    assert goal.target_questions == 300
    assert goal.target_hours is None


def test_create_weekly_goal_with_hours_and_questions(
    client,
    db_session,
    test_user,
):
    """Deve permitir meta combinada."""

    response = client.post(
        "/api/goals/",
        json={
            "user_id": test_user.id,
            "target_hours": 10,
            "target_questions": 300,
        },
    )

    assert response.status_code == 201

    goal = db_session.query(Goal).filter_by(
        user_id=test_user.id
    ).first()

    assert goal.target_hours == 10
    assert goal.target_questions == 300


# ==========================================================
# VALIDATIONS
# ==========================================================

def test_create_goal_without_any_target(client, test_user):
    """
    Não deve criar goal sem nenhuma meta.
    """

    response = client.post(
        "/api/goals/",
        json={
            "user_id": test_user.id,
        },
    )

    assert response.status_code == 400


def test_create_goal_negative_hours(client, test_user):

    response = client.post(
        "/api/goals/",
        json={
            "user_id": test_user.id,
            "target_hours": -5,
        },
    )

    assert response.status_code == 400


def test_create_goal_negative_questions(client, test_user):

    response = client.post(
        "/api/goals/",
        json={
            "user_id": test_user.id,
            "target_questions": -10,
        },
    )

    assert response.status_code == 400


def test_create_goal_invalid_user(client):

    response = client.post(
        "/api/goals/",
        json={
            "user_id": 999999,
            "target_hours": 10,
        },
    )

    assert response.status_code == 404


# ==========================================================
# DUPLICITY
# ==========================================================

def test_create_second_goal_same_week(client, test_user):
    """
    Não permite dois registros Goal
    para o mesmo usuário na mesma semana.
    """

    response = client.post(
        "/api/goals/",
        json={
            "user_id": test_user.id,
            "target_hours": 10,
        },
    )

    assert response.status_code == 201


    response = client.post(
        "/api/goals/",
        json={
            "user_id": test_user.id,
            "target_questions": 300,
        },
    )

    assert response.status_code == 409


# ==========================================================
# UPDATE
# ==========================================================

def test_update_existing_goal_add_questions(
    client,
    db_session,
    test_user,
):
    """
    Usuário pode complementar uma meta existente.
    Não cria outro registro.
    """

    goal = Goal(
        user_id=test_user.id,
        target_hours=10,
        target_questions=None,
        year=2026,
        week_number=30,
    )

    db_session.add(goal)
    db_session.commit()


    response = client.put(
        f"/api/goals/{goal.id}",
        json={
            "target_questions":300,
        },
    )

    assert response.status_code == 200


    db_session.refresh(goal)

    assert goal.target_hours == 10
    assert goal.target_questions == 300



# ==========================================================
# REMOVE GOAL
# ==========================================================

def test_remove_goal_when_targets_zero(
    client,
    db_session,
    test_user,
):
    """
    Quando usuário informa zero para todas as metas,
    a meta semanal deve ser removida.
    """

    goal = Goal(
        user_id=test_user.id,
        target_hours=10,
        target_questions=300,
        year=2026,
        week_number=30,
    )

    db_session.add(goal)
    db_session.commit()

    goal_id = goal.id


    response = client.put(
        f"/api/goals/{goal_id}",
        json={
            "target_hours":0,
            "target_questions":0,
        },
    )


    assert response.status_code == 200


    db_session.expire_all()

    assert db_session.get(Goal, goal_id) is None