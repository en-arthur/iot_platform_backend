import pytest
from fastapi import APIRouter, Depends
from app.core.auth import get_current_user
from app.models.auth import AuthUser
from app.main import app

# Register a temporary test route to test auth dependency
auth_test_router = APIRouter()


@auth_test_router.get("/api/v1/test-auth")
async def protected_route(user: AuthUser = Depends(get_current_user)):
    return {"user_id": user.id, "email": user.email, "role": user.role}


app.include_router(auth_test_router)


def test_missing_auth_header(client):
    response = client.get("/api/v1/test-auth")
    assert response.status_code == 401
    assert "Missing Authorization header" in response.text


def test_invalid_bearer_format(client):
    response = client.get("/api/v1/test-auth", headers={"Authorization": "InvalidToken123"})
    assert response.status_code == 401
    assert "Authorization header must be 'Bearer <token>'" in response.text


def test_expired_jwt_token(client, create_test_token):
    expired_token = create_test_token(expired=True)
    response = client.get(
        "/api/v1/test-auth",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert "expired" in response.text.lower()


def test_valid_jwt_token(client, create_test_token):
    valid_token = create_test_token(user_id="user-456")
    response = client.get(
        "/api/v1/test-auth",
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user-456"
    assert data["email"] == "user-456@example.com"
    assert data["role"] == "authenticated"


def test_dev_mock_token(client):
    response = client.get(
        "/api/v1/test-auth",
        headers={"Authorization": "Bearer mock-user-dev-789"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "dev-789"
