# tests/conftest.py

import pytest
import uuid
from app import create_app
from app.database import Base, engine, SessionLocal
from werkzeug.security import generate_password_hash
from app.models.user import User


@pytest.fixture(scope="session")
def app():
    """Cria a aplicação Flask para testes."""
    app = create_app(testing=True)
    app.config["TESTING"] = True
    return app


@pytest.fixture(scope="session")
def setup_database():
    """Cria o schema do banco para os testes."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(setup_database):
    """Cria uma sessão isolada para cada teste."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(app, db_session):
    """Cliente HTTP para testes."""
    
    from app import database

    # override da sessão
    database.SessionLocal = lambda: db_session

    with app.test_client(use_cookies=True) as client:
        with app.app_context():
            yield client

@pytest.fixture
def test_user(db_session):
    """
    Cria um usuário padrão para testes.
    """

    user = User(
        username="Test User",
        email=f"{uuid.uuid4()}@example.com",
        password_hash=generate_password_hash("123456"),
    )

    db_session.add(user)
    db_session.commit()

    return user


@pytest.fixture
def authenticated_client(client, test_user):
    """
    Retorna cliente autenticado como test_user.
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