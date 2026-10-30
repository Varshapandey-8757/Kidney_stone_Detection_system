import os
import shutil
import tempfile
from pathlib import Path

_test_root = Path(tempfile.mkdtemp(prefix="kidney-stone-tests-"))
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-validation"
os.environ["DATABASE_URL"] = f"sqlite:///{(_test_root / 'test.db').as_posix()}"
os.environ["MODEL_PATH"] = str(_test_root / "missing-model.keras")
os.environ["APP_ENV"] = "test"
os.environ.pop("ADMIN_EMAIL", None)
os.environ.pop("ADMIN_PASSWORD", None)

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.main import app
from app.models.user import User
from app.services import ml_service


def pytest_sessionfinish(session, exitstatus):
    engine.dispose()
    shutil.rmtree(_test_root, ignore_errors=True)


@pytest.fixture
def client(tmp_path, monkeypatch):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    settings.REFRESH_COOKIE_PATH = "/auth"
    ml_service.model = None

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(engine)


@pytest.fixture
def make_user():
    def create(email="person@example.com", role="user", active=True):
        with SessionLocal() as db:
            user = User(
                name="Test Person",
                email=email,
                password_hash=hash_password("Strong-Pass-123"),
                role=role,
                is_active=active,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user.id

    return create


@pytest.fixture
def auth_headers(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "Test Person",
            "email": "person@example.com",
            "password": "Strong-Pass-123",
        },
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
