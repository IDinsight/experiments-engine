import os
from typing import AsyncGenerator, Generator

from fastapi.testclient import TestClient
from pytest import FixtureRequest, fixture, mark
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.messages.models import MessageDB

base_mab_payload = {
    "name": "Test",
    "description": "Test description",
    "prior_type": "beta",
    "reward_type": "binary",
    "arms": [
        {
            "name": "arm 1",
            "description": "arm 1 description",
            "alpha_init": 5,
            "beta_init": 1,
        },
        {
            "name": "arm 2",
            "description": "arm 2 description",
            "alpha_init": 1,
            "beta_init": 4,
        },
    ],
    "notifications": {
        "onTrialCompletion": True,
        "numberOfTrials": 2,
        "onDaysElapsed": False,
        "daysElapsed": 3,
        "onPercentBetter": False,
        "percentBetterThreshold": 5,
    },
}


@fixture
def admin_token(client: TestClient) -> str:
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
def experiment_id(client: TestClient, admin_token: str) -> Generator[int, None, None]:
    response = client.post(
        "/mab",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=base_mab_payload,
    )
    yield response.json()["experiment_id"]
    client.delete(
        f"/mab/{response.json()['experiment_id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )


@fixture
def message_payload(experiment_id: int) -> dict:
    return {
        "text": "test message",
        "title": "test title",
        "experiment_id": experiment_id,
    }


class TestMessages:
    @fixture
    async def messages(
        self,
        request: FixtureRequest,
        admin_token: str,
        client: TestClient,
        message_payload: dict,
        asession: AsyncSession,
    ) -> AsyncGenerator[list, None]:
        n_messages = request.param
        all_messages = []
        for _ in range(n_messages):
            response = client.post(
                "/messages",
                headers={"Authorization": f"Bearer {admin_token}"},
                json=message_payload,
            )
            all_messages.append(response.json()["message_id"])

        yield all_messages
        await MessageDB.delete_messages_by_message_ids(asession, all_messages, 1)

    @mark.parametrize(
        "messages, n_messages", [(3, 3), (4, 4), (1, 1)], indirect=["messages"]
    )
    def test_get_messsages(
        self, client: TestClient, admin_token: str, n_messages: int, messages: list
    ) -> None:
        response = client.get(
            "/messages", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert len(response.json()) == n_messages

    @mark.parametrize(
        "messages, n_read", [(4, 3), (4, 4), (2, 0)], indirect=["messages"]
    )
    def test_mark_messages_as_read(
        self, messages: list, client: TestClient, admin_token: str, n_read: int
    ) -> None:
        response = client.get(
            "/messages", headers={"Authorization": f"Bearer {admin_token}"}
        )
        unread_messages = sum([m.get("is_unread") for m in response.json()])
        assert unread_messages == len(messages)

        messages_ids = [m["message_id"] for m in response.json()][:n_read]

        response = client.patch(
            "/messages",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"message_ids": messages_ids, "is_unread": False},
        )

        unread_messages = sum([m.get("is_unread") for m in response.json()])
        assert unread_messages == len(messages) - n_read
