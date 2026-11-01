import pytest
import jwt
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

TEST_JWT_SECRET = "test-jwt-secret-key-for-unit-tests-12345"


@pytest.fixture(autouse=True)
def override_settings():
    settings.ENVIRONMENT = "test"
    settings.SUPABASE_JWT_SECRET = TEST_JWT_SECRET


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def create_test_token():
    def _generator(user_id: str = "test-user-uuid-1", expired: bool = False):
        exp = datetime.now(timezone.utc) + (
            timedelta(hours=1) if not expired else timedelta(hours=-1)
        )
        payload = {
            "sub": user_id,
            "email": f"{user_id}@example.com",
            "role": "authenticated",
            "aud": "authenticated",
            "exp": int(exp.timestamp()),
        }
        return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")

    return _generator
