import os

from fastapi.testclient import TestClient
from pytest import fixture

from .config import TEST_PASSWORD, TEST_USER_API_KEY, TEST_USERNAME


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
    def user_token(self, client: TestClient, regular_user: int) -> str:
        response = client.post(
            "/login",
            data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
        )
        token = response.json()["access_token"]
        return token

    def test_user_id_1_can_create_user(self, client: TestClient) -> None:
        response = client.post(
            "/user/", json={"username": "user_test", "password": "password_test"}
        )

        assert response.status_code == 200

    def test_user_id_2_cannot_create_user(self, client: TestClient) -> None:
        # Register a user
        response = client.post(
            "/user/",
            json={"username": "user_test1", "password": "password_test"},
        )
        assert response.status_code == 200

        # Try to register another user
        response = client.post(
            "/user/",
            json={"username": "user_test1", "password": "password_test"},
        )
        assert response.status_code == 400

    def test_get_current_user(
        self, client: TestClient, user_token: str, regular_user: int
    ) -> None:
        response = client.get(
            "/user/",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        assert response.json()["user_id"] == regular_user
        assert response.json()["username"] == TEST_USERNAME

    def test_rotate_key(self, client: TestClient, user_token: str) -> None:
        response = client.get(
            "/user/", headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        assert response.json()["api_key_first_characters"] == TEST_USER_API_KEY[:5]

        response = client.put(
            "/user/rotate-key", headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        assert response.json()["new_api_key"] != TEST_USER_API_KEY
