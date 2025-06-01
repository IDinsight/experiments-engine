import os
from typing import Annotated, Generator, cast
from unittest.mock import MagicMock, patch

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pytest import fixture
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.dependencies import get_current_user, get_verified_user
from backend.app.database import get_async_session
from backend.app.users.models import UserDB
from backend.app.workspaces.models import UserRoles

from .config import TEST_PASSWORD


@fixture
def mock_send_email() -> Generator[MagicMock, None, None]:
    with patch("backend.app.email.EmailService._send_email") as mocked_send:
        mocked_send.return_value = {"MessageId": "mock-message-id"}
        yield mocked_send


class TestWorkspace:
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

    @fixture
    def mock_async_session(self, client: TestClient) -> Generator[None, None, None]:
        async def override_get_async_session() -> AsyncSession:
            # This would need to be implemented to return a test async session
            pass

        app = cast(FastAPI, client.app)
        app.dependency_overrides[get_async_session] = override_get_async_session
        yield
        app.dependency_overrides.clear()

    def test_get_current_workspace(
        self, client: TestClient, user_token: str, mock_verified_user: None
    ) -> None:
        response = client.get(
            "/workspace/current",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        assert "workspace_name" in response.json()
        assert "is_default" in response.json()
        assert response.json()["is_default"] is True

    def test_retrieve_all_workspaces(
        self, client: TestClient, user_token: str, mock_verified_user: None
    ) -> None:
        response = client.get(
            "/workspace/",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        # At least one workspace (default) should exist
        assert len(response.json()) >= 1

    def test_create_workspace(
        self, client: TestClient, user_token: str, mock_verified_user: None
    ) -> None:
        workspace_name = "Test Workspace Creation"
        response = client.post(
            "/workspace/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "workspace_name": workspace_name,
                "api_daily_quota": 1000,
                "content_quota": 50,
            },
        )
        assert response.status_code == 200
        assert response.json()["workspace_name"] == workspace_name
        assert response.json()["api_daily_quota"] == 1000
        assert response.json()["content_quota"] == 50

        # Verify the workspace exists in the list of workspaces
        response = client.get(
            "/workspace/",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        workspaces = response.json()
        assert any(ws["workspace_name"] == workspace_name for ws in workspaces)

    def test_update_workspace(
        self, client: TestClient, user_token: str, mock_verified_user: None
    ) -> None:
        # First create a workspace
        original_name = "Original Workspace Name"
        response = client.post(
            "/workspace/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"workspace_name": original_name},
        )
        assert response.status_code == 200
        workspace_id = response.json()["workspace_id"]

        # Now update the workspace name
        new_name = "Updated Workspace Name"
        response = client.put(
            f"/workspace/{workspace_id}",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"workspace_name": new_name},
        )
        assert response.status_code == 200
        assert response.json()["workspace_name"] == new_name

        # Verify the workspace has been updated in the list
        response = client.get(
            "/workspace/",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        workspaces = response.json()
        assert any(ws["workspace_name"] == new_name for ws in workspaces)
        assert not any(ws["workspace_name"] == original_name for ws in workspaces)

    def test_switch_workspace(
        self, client: TestClient, user_token: str, mock_verified_user: None
    ) -> None:
        # First create a new workspace
        workspace_name = "Test Switch Workspace"
        response = client.post(
            "/workspace/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"workspace_name": workspace_name},
        )
        assert response.status_code == 200

        # Now switch to the new workspace
        response = client.post(
            "/workspace/switch",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"workspace_name": workspace_name},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

        # Verify that the current workspace is now the one we switched to
        new_token = response.json()["access_token"]
        response = client.get(
            "/workspace/current",
            headers={"Authorization": f"Bearer {new_token}"},
        )
        assert response.status_code == 200
        assert response.json()["workspace_name"] == workspace_name

    def test_rotate_workspace_api_key(
        self, client: TestClient, user_token: str, mock_verified_user: None
    ) -> None:
        response = client.put(
            "/workspace/rotate-key",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        assert "new_api_key" in response.json()
        assert "workspace_name" in response.json()

    def test_invite_user_to_workspace(
        self,
        client: TestClient,
        user_token: str,
        mock_verified_user: None,
        mock_send_email: MagicMock,
    ) -> None:
        # First create a non-default workspace
        workspace_name = "Test Invite Workspace"
        response = client.post(
            "/workspace/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"workspace_name": workspace_name},
        )
        assert response.status_code == 200

        # Now invite a user to this workspace
        invite_email = (
            f"invited_user_{os.urandom(4).hex()}@example.com"  # Use unique email
        )
        response = client.post(
            "/workspace/invite",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "workspace_name": workspace_name,
                "email": invite_email,
                "role": UserRoles.READ_ONLY,
            },
        )
        assert response.status_code == 200
        assert response.json()["email"] == invite_email
        assert response.json()["workspace_name"] == workspace_name
        assert "message" in response.json()

        # Verify that email was called
        mock_send_email.assert_called_once()

    def test_get_workspace_users(
        self, client: TestClient, user_token: str, mock_verified_user: None
    ) -> None:
        # First create a workspace
        workspace_name = "Test Workspace Users"
        response = client.post(
            "/workspace/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"workspace_name": workspace_name},
        )
        assert response.status_code == 200
        workspace_id = response.json()["workspace_id"]

        # Get users in workspace
        response = client.get(
            f"/workspace/{workspace_id}/users",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        # Creator should be in the workspace with ADMIN role
        users = response.json()
        assert len(users) >= 1
        # Since username is now dynamic, just check that at least one user
        # has ADMIN role
        assert any(user["role"] == UserRoles.ADMIN for user in users)

    def test_get_workspace_by_id(
        self, client: TestClient, user_token: str, mock_verified_user: None
    ) -> None:
        # First create a workspace
        workspace_name = "Test Get Workspace"
        response = client.post(
            "/workspace/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"workspace_name": workspace_name},
        )
        assert response.status_code == 200
        workspace_id = response.json()["workspace_id"]

        # Get workspace by ID
        response = client.get(
            f"/workspace/{workspace_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        assert response.json()["workspace_id"] == workspace_id
        assert response.json()["workspace_name"] == workspace_name

    def test_get_workspace_key_history(
        self, client: TestClient, user_token: str, mock_verified_user: None
    ) -> None:
        # First create a workspace
        workspace_name = "Test Key History"
        response = client.post(
            "/workspace/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"workspace_name": workspace_name},
        )
        assert response.status_code == 200
        workspace_id = response.json()["workspace_id"]

        # Rotate API key to create a history record
        response = client.put(
            "/workspace/rotate-key",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200

        # Wait a moment to ensure DB transactions complete
        import time

        time.sleep(0.5)

        # Switch to the newly created workspace
        response = client.post(
            "/workspace/switch",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"workspace_name": workspace_name},
        )
        assert response.status_code == 200
        new_token = response.json()["access_token"]

        # Now rotate the key for this specific workspace
        response = client.put(
            "/workspace/rotate-key",
            headers={"Authorization": f"Bearer {new_token}"},
        )
        assert response.status_code == 200

        # Get key rotation history
        response = client.get(
            f"/workspace/{workspace_id}/key-history",
            headers={"Authorization": f"Bearer {new_token}"},
        )
        assert response.status_code == 200

        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1
