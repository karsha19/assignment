import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from app.db.session import Base
from app import main as app_main
from app.db import session as db_session_module
from fastapi.testclient import TestClient

TEST_ENGINE = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app_main.app.dependency_overrides[db_session_module.get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def client():
    return TestClient(app_main.app)


@pytest.fixture
def db():
    return TestingSessionLocal()


@pytest.fixture
def admin_token(client, db):
    from app.models.models import User, RoleEnum
    from app.core.security import hash_password

    user = User(username="admin", hashed_password=hash_password("Admin@123"), role=RoleEnum.admin)
    db.add(user)
    db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin@123"})
    return resp.json()["access_token"]


@pytest.fixture
def operator_token(client, db):
    from app.models.models import User, RoleEnum
    from app.core.security import hash_password

    user = User(username="operator", hashed_password=hash_password("Operator@123"), role=RoleEnum.operator)
    db.add(user)
    db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "operator", "password": "Operator@123"})
    return resp.json()["access_token"]
