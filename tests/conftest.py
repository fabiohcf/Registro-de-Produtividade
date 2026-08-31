# tests/conftest.py

import pytest
import uuid

from werkzeug.security import generate_password_hash

from app import create_app
from app.database import Base, engine, SessionLocal
from app.models.user import User


@pytest.fixture(scope="session")
def app():
    """Cria a aplicação Flask para testes."""

    app = create_app(testing=True)
    app.config["TESTING"] = True

    return app


@pytest.fixture
def setup_database():
    """
    Cria um banco de testes limpo para cada teste.
    """

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(setup_database):
    """
    Cria uma sessão independente para cada teste.

    A sessão pertence exclusivamente ao teste.
    """

    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(app, setup_database):
    """
    Cliente HTTP para testes.

    A aplicação utiliza sua própria SessionLocal,
    exatamente como utilizaria em produção.
    """

    with app.test_client(use_cookies=True) as client:
        with app.app_context():
            yield client


@pytest.fixture
def test_user(db_session):
    """
    Cria um usuário exclusivo para o teste.
    """

    user = User(
        username=f"TestUser_{uuid.uuid4().hex[:8]}",
        email=f"{uuid.uuid4()}@example.com",
        password_hash=generate_password_hash("123456"),
    )

    db_session.add(user)
    db_session.commit()

    return user



@pytest.fixture
def other_user(db_session):
    """
    Cria um segundo usuário para testes de isolamento e ownership.
    """

    user = User(
        username=f"OtherUser_{uuid.uuid4().hex[:8]}",
        email=f"{uuid.uuid4()}@example.com",
        password_hash=generate_password_hash("123456"),
    )

    db_session.add(user)
    db_session.commit()

    return user



@pytest.fixture
def authenticated_client(client, test_user):
    """
    Retorna um cliente autenticado como test_user.
    """

    response = client.post(
        "/auth/login",
        json={
            "username": test_user.username,
            "password": "123456",
        },
    )

    assert response.status_code == 200

    return client