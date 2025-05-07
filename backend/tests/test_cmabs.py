import copy
import os
from typing import Generator

import numpy as np
from fastapi.testclient import TestClient
from pytest import FixtureRequest, fixture, mark
from sqlalchemy.orm import Session

from backend.app.contextual_mab.models import (
    ContextDB,
    ContextualArmDB,
    ContextualBanditDB,
)
from backend.app.models import NotificationsDB

base_normal_payload = {
    "name": "Test",
    "description": "Test description",
    "prior_type": "normal",
    "reward_type": "real-valued",
    "sticky_assignment": False,
    "arms": [
        {
            "name": "arm 1",
            "description": "arm 1 description",
            "mu_init": 0,
            "sigma_init": 1,
        },
        {
            "name": "arm 2",
            "description": "arm 2 description",
            "mu_init": 0,
            "sigma_init": 1,
        },
    ],
    "contexts": [
        {
            "name": "Context 1",
            "description": "context 1 description",
            "value_type": "binary",
        },
        {
            "name": "Context 2",
            "description": "context 2 description",
            "value_type": "real-valued",
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

base_binary_normal_payload = base_normal_payload.copy()
base_binary_normal_payload["reward_type"] = "binary"


@fixture
def clean_cmabs(db_session: Session) -> Generator:
    yield
    db_session.query(NotificationsDB).delete()
    db_session.query(ContextualArmDB).delete()
    db_session.query(ContextDB).delete()
    db_session.query(ContextualBanditDB).delete()
    db_session.commit()


class TestCMab:
    @fixture
    def create_cmab_payload(self, request: FixtureRequest) -> dict:
        payload_normal: dict = copy.deepcopy(base_normal_payload)
        payload_normal["arms"] = list(payload_normal["arms"])
        payload_normal["contexts"] = list(payload_normal["contexts"])

        payload_binary_normal: dict = copy.deepcopy(base_binary_normal_payload)
        payload_binary_normal["arms"] = list(payload_binary_normal["arms"])
        payload_binary_normal["contexts"] = list(payload_binary_normal["contexts"])

        if request.param == "base_normal":
            return payload_normal
        if request.param == "base_binary_normal":
            return payload_binary_normal
        if request.param == "one_arm":
            payload_normal["arms"].pop()
            return payload_normal
        if request.param == "no_notifications":
            payload_normal["notifications"]["onTrialCompletion"] = False
            return payload_normal
        if request.param == "invalid_prior":
            payload_normal["prior_type"] = "beta"
            return payload_normal
        if request.param == "invalid_reward":
            payload_normal["reward_type"] = "invalid"
            return payload_normal
        if request.param == "invalid_sigma":
            payload_normal["arms"][0]["sigma_init"] = 0
            return payload_normal
        if request.param == "with_sticky_assignment":
            payload_normal["sticky_assignment"] = True
            return payload_normal

        else:
            raise ValueError("Invalid parameter")

    @mark.parametrize(
        "create_cmab_payload, expected_response",
        [
            ("base_normal", 200),
            ("base_binary_normal", 200),
            ("one_arm", 422),
            ("no_notifications", 200),
            ("invalid_prior", 422),
            ("invalid_reward", 422),
            ("invalid_sigma", 422),
        ],
        indirect=["create_cmab_payload"],
    )
    def test_create_cmab(
        self,
        create_cmab_payload: dict,
        client: TestClient,
        expected_response: int,
        admin_token: str,
        clean_cmabs: None,
    ) -> None:
        response = client.post(
            "/contextual_mab",
            json=create_cmab_payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == expected_response

    @fixture
    def create_cmabs(
        self,
        client: TestClient,
        admin_token: str,
        request: FixtureRequest,
        create_cmab_payload: dict,
    ) -> Generator:
        cmabs = []
        n_cmabs = request.param if hasattr(request, "param") else 1
        for _ in range(n_cmabs):
            response = client.post(
                "/contextual_mab",
                json=create_cmab_payload,
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            cmabs.append(response.json())
        yield cmabs
        for cmab in cmabs:
            client.delete(
                f"/contextual_mab/{cmab['experiment_id']}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

    @mark.parametrize(
        "create_cmabs, n_expected, create_cmab_payload",
        [(0, 0, "base_normal"), (2, 2, "base_normal"), (5, 5, "base_normal")],
        indirect=["create_cmabs", "create_cmab_payload"],
    )
    def test_get_all_cmabs(
        self,
        client: TestClient,
        admin_token: str,
        n_expected: int,
        create_cmab_payload: dict,
        create_cmabs: list,
    ) -> None:
        response = client.get(
            "/contextual_mab", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert len(response.json()) == n_expected

    @mark.parametrize(
        "create_cmabs, expected_response, create_cmab_payload",
        [(0, 404, "base_normal"), (2, 200, "base_normal")],
        indirect=["create_cmabs", "create_cmab_payload"],
    )
    def test_get_cmab(
        self,
        client: TestClient,
        admin_token: str,
        create_cmab_payload: dict,
        create_cmabs: list,
        expected_response: int,
    ) -> None:
        id = create_cmabs[0]["experiment_id"] if create_cmabs else 999

        response = client.get(
            f"/contextual_mab/{id}", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == expected_response

    @mark.parametrize("create_cmab_payload", ["base_normal"], indirect=True)
    def test_draw_arm_draw_id_provided(
        self, client: TestClient, create_cmabs: list, create_cmab_payload: dict
    ) -> None:
        id = create_cmabs[0]["experiment_id"]
        api_key = os.environ.get("ADMIN_API_KEY", "")
        response = client.post(
            f"/contextual_mab/{id}/draw",
            headers={"Authorization": f"Bearer {api_key}"},
            params={"draw_id": "test_draw_id"},
            json=[
                {"context_id": 1, "context_value": 0},
                {"context_id": 2, "context_value": 0.5},
            ],
        )
        assert response.status_code == 200
        assert response.json()["draw_id"] == "test_draw_id"

    @mark.parametrize("create_cmab_payload", ["base_normal"], indirect=True)
    def test_draw_arm_no_draw_id_provided(
        self, client: TestClient, create_cmabs: list, create_cmab_payload: dict
    ) -> None:
        id = create_cmabs[0]["experiment_id"]
        api_key = os.environ.get("ADMIN_API_KEY", "")
        response = client.post(
            f"/contextual_mab/{id}/draw",
            headers={"Authorization": f"Bearer {api_key}"},
            json=[
                {"context_id": 1, "context_value": 0},
                {"context_id": 2, "context_value": 0.5},
            ],
        )
        assert response.status_code == 200
        assert len(response.json()["draw_id"]) == 36

    @mark.parametrize(
        "create_cmab_payload, client_id, expected_response",
        [
            ("with_sticky_assignment", None, 400),
            ("with_sticky_assignment", "test_client_id", 200),
        ],
        indirect=["create_cmab_payload"],
    )
    def test_draw_arm_sticky_assignment_client_id_provided(
        self,
        client: TestClient,
        create_cmabs: list,
        create_cmab_payload: dict,
        client_id: str | None,
        expected_response: int,
    ) -> None:
        id = create_cmabs[0]["experiment_id"]
        api_key = os.environ.get("ADMIN_API_KEY", "")
        url = f"/contextual_mab/{id}/draw"
        if client_id:
            url += f"?client_id={client_id}"

        response = client.post(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            json=[
                {"context_id": 1, "context_value": 0},
                {"context_id": 2, "context_value": 0.5},
            ],
        )
        assert response.status_code == expected_response

    @mark.parametrize("create_cmab_payload", ["with_sticky_assignment"], indirect=True)
    def test_draw_arm_with_sticky_assignment(
        self, client: TestClient, create_cmabs: list, create_cmab_payload: dict
    ) -> None:
        id = create_cmabs[0]["experiment_id"]
        api_key = os.environ.get("ADMIN_API_KEY", "")
        arm_ids = []

        for _ in range(10):
            response = client.post(
                f"/contextual_mab/{id}/draw?client_id=123",
                headers={"Authorization": f"Bearer {api_key}"},
                json=[
                    {"context_id": 1, "context_value": 0},
                    {"context_id": 2, "context_value": 1},
                ],
            )
            arm_ids.append(response.json()["arm"]["arm_id"])

        assert np.unique(arm_ids).size == 1

    @mark.parametrize("create_cmab_payload", ["base_normal"], indirect=True)
    def test_one_outcome_per_draw(
        self, client: TestClient, create_cmabs: list, create_cmab_payload: dict
    ) -> None:
        id = create_cmabs[0]["experiment_id"]
        api_key = os.environ.get("ADMIN_API_KEY", "")
        response = client.post(
            f"/contextual_mab/{id}/draw",
            headers={"Authorization": f"Bearer {api_key}"},
            json=[
                {"context_id": 1, "context_value": 0},
                {"context_id": 2, "context_value": 0.5},
            ],
        )
        assert response.status_code == 200
        draw_id = response.json()["draw_id"]

        response = client.put(
            f"/contextual_mab/{id}/{draw_id}/1",
            headers={"Authorization": f"Bearer {api_key}"},
        )

        assert response.status_code == 200

        response = client.put(
            f"/contextual_mab/{id}/{draw_id}/1",
            headers={"Authorization": f"Bearer {api_key}"},
        )

        assert response.status_code == 400

    @mark.parametrize(
        "n_draws, create_cmab_payload",
        [(0, "base_normal"), (1, "base_normal"), (5, "base_normal")],
        indirect=["create_cmab_payload"],
    )
    def test_get_outcomes(
        self,
        client: TestClient,
        create_cmabs: list,
        n_draws: int,
        create_cmab_payload: dict,
    ) -> None:
        id = create_cmabs[0]["experiment_id"]
        api_key = os.environ.get("ADMIN_API_KEY", "")
        id = create_cmabs[0]["experiment_id"]

        for _ in range(n_draws):
            response = client.post(
                f"/contextual_mab/{id}/draw",
                headers={"Authorization": f"Bearer {api_key}"},
                json=[
                    {"context_id": 1, "context_value": 0},
                    {"context_id": 2, "context_value": 0.5},
                ],
            )
            assert response.status_code == 200
            draw_id = response.json()["draw_id"]
            response = client.put(
                f"/contextual_mab/{id}/{draw_id}/1",
                headers={"Authorization": f"Bearer {api_key}"},
            )

        response = client.get(
            f"/contextual_mab/{id}/outcomes",
            headers={"Authorization": f"Bearer {api_key}"},
        )

        assert response.status_code == 200
        assert len(response.json()) == n_draws


class TestNotifications:
    @fixture()
    def create_cmab_payload(self, request: FixtureRequest) -> dict:
        payload: dict = copy.deepcopy(base_normal_payload)
        payload["arms"] = list(payload["arms"])
        payload["contexts"] = list(payload["contexts"])

        match request.param:
            case "base":
                pass
            case "daysElapsed_only":
                payload["notifications"]["onTrialCompletion"] = False
                payload["notifications"]["onDaysElapsed"] = True
            case "trialCompletion_only":
                payload["notifications"]["onTrialCompletion"] = True
            case "percentBetter_only":
                payload["notifications"]["onTrialCompletion"] = False
                payload["notifications"]["onPercentBetter"] = True
            case "all_notifications":
                payload["notifications"]["onDaysElapsed"] = True
                payload["notifications"]["onPercentBetter"] = True
            case "no_notifications":
                payload["notifications"]["onTrialCompletion"] = False
            case "daysElapsed_missing":
                payload["notifications"]["daysElapsed"] = 0
                payload["notifications"]["onDaysElapsed"] = True
            case "trialCompletion_missing":
                payload["notifications"]["numberOfTrials"] = 0
                payload["notifications"]["onTrialCompletion"] = True
            case "percentBetter_missing":
                payload["notifications"]["percentBetterThreshold"] = 0
                payload["notifications"]["onPercentBetter"] = True
            case _:
                raise ValueError("Invalid parameter")

        return payload

    @mark.parametrize(
        "create_cmab_payload, expected_response",
        [
            ("base", 200),
            ("daysElapsed_only", 200),
            ("trialCompletion_only", 200),
            ("percentBetter_only", 200),
            ("all_notifications", 200),
            ("no_notifications", 200),
            ("daysElapsed_missing", 422),
            ("trialCompletion_missing", 422),
            ("percentBetter_missing", 422),
        ],
        indirect=["create_cmab_payload"],
    )
    def test_notifications(
        self,
        client: TestClient,
        admin_token: str,
        create_cmab_payload: dict,
        expected_response: int,
        clean_cmabs: None,
    ) -> None:
        response = client.post(
            "/contextual_mab",
            json=create_cmab_payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == expected_response
