import os
from typing import Annotated, Generator, cast
from unittest.mock import MagicMock, patch

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pytest import fixture

from backend.app.auth.dependencies import get_current_user, get_verified_user
from backend.app.users.models import UserDB

from .config import TEST_PASSWORD


@fixture
def mock_send_email() -> Generator[MagicMock, None, None]:
    with patch("backend.app.email.EmailService._send_email") as mocked_send:
        mocked_send.return_value = {"MessageId": "mock-message-id"}
        yield mocked_send


class TestCreateUser:
    @fixture
    def admin_token(self, client: TestClient) -> str:
        response = client.post(
            "/login",
            data={
                "username": os.environ.get("ADMIN_USERNAME", ""),
                "password": os.environ.get("ADMIN_PASSWORD", ""),
            },
        )
        token = response.json()["access_token"]
        return token

    @fixture
    def user_token(self, client: TestClient, regular_user: tuple) -> str:
        user_id, username, _ = regular_user
        response = client.post(
            "/login",
            data={"username": username, "password": TEST_PASSWORD},
        )
        token = response.json()["access_token"]
        return token

    @fixture
    def mock_verified_user(self, client: TestClient) -> Generator[None, None, None]:
        async def mock_get_verified_user(
            user_db: Annotated[UserDB, Depends(get_current_user)],
        ) -> UserDB:
            return user_db

        app = cast(FastAPI, client.app)
        app.dependency_overrides[get_verified_user] = mock_get_verified_user
        yield
        app.dependency_overrides.clear()

    def test_user_id_1_can_create_user(
        self, client: TestClient, mock_send_email: MagicMock
    ) -> None:
        response = client.post(
            "/user/",
            json={
                "username": "user_test",
                "password": "password_test",
                "first_name": "Test",
                "last_name": "User",
            },
        )

        assert response.status_code == 200

    def test_user_id_2_cannot_create_user(
        self, client: TestClient, mock_send_email: MagicMock
    ) -> None:
        # Register a user
        username = f"user_test1_{os.urandom(4).hex()}"
        response = client.post(
            "/user/",
            json={
                "username": username,
                "password": "password_test",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        assert response.status_code == 200

        # Try to register another user with the same username
        response = client.post(
            "/user/",
            json={
                "username": username,
                "password": "password_test",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        assert response.status_code == 400

    def test_get_current_user(
        self, client: TestClient, user_token: str, regular_user: tuple
    ) -> None:
        user_id, username, _ = regular_user
        response = client.get(
            "/user/",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        assert response.json()["user_id"] == user_id
        assert response.json()["username"] == username

    def test_login_creates_default_workspace(
        self, client: TestClient, mock_send_email: MagicMock
    ) -> None:
        # Register a new user
        test_username = f"workspace_user_{os.urandom(4).hex()}@test.com"
        response = client.post(
            "/user/",
            json={
                "username": test_username,
                "password": "password_test",
                "first_name": "Workspace",
                "last_name": "User",
            },
        )
        assert response.status_code == 200

        # Login with the new user
        response = client.post(
            "/login",
            data={"username": test_username, "password": "password_test"},
        )
        assert response.status_code == 200
        token = response.json()["access_token"]

        # Check if a default workspace was created for the user
        response = client.get(
            "/workspace/current",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["workspace_name"] == f"{test_username}'s Workspace"
        assert response.json()["is_default"] is True
