import copy
import os
from typing import Generator

import numpy as np
from fastapi.testclient import TestClient
from pytest import FixtureRequest, fixture, mark
from sqlalchemy.orm import Session

from backend.app.bayes_ab.models import BayesianABArmDB, BayesianABDB
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
            "is_treatment_arm": True,
        },
        {
            "name": "arm 2",
            "description": "arm 2 description",
            "mu_init": 2,
            "sigma_init": 2,
            "is_treatment_arm": False,
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
def clean_bayes_ab(db_session: Session) -> Generator:
    """
    Fixture to clean the database before each test.
    """
    yield
    db_session.query(NotificationsDB).delete()
    db_session.query(BayesianABArmDB).delete()
    db_session.query(BayesianABDB).delete()

    db_session.commit()


class TestBayesAB:
    """
    Test class for Bayesian A/B testing.
    """

    @fixture
    def create_bayes_ab_payload(self, request: FixtureRequest) -> dict:
        """
        Fixture to create a payload for the Bayesian A/B test.
        """
        payload_normal: dict = copy.deepcopy(base_normal_payload)
        payload_normal["arms"] = list(payload_normal["arms"])

        payload_binary_normal: dict = copy.deepcopy(base_binary_normal_payload)
        payload_binary_normal["arms"] = list(payload_binary_normal["arms"])

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
        if request.param == "invalid_sigma":
            payload_normal["arms"][0]["sigma_init"] = 0
            return payload_normal
        if request.param == "invalid_params":
            payload_normal["arms"][0].pop("mu_init")
            return payload_normal
        if request.param == "two_treatment_arms":
            payload_normal["arms"][0]["is_treatment_arm"] = True
            payload_normal["arms"][1]["is_treatment_arm"] = True
            return payload_normal
        if request.param == "with_sticky_assignment":
            payload_normal["sticky_assignment"] = True
            return payload_normal
        else:
            raise ValueError("Invalid parameter")

    @fixture
    def create_bayes_abs(
        self,
        client: TestClient,
        admin_token: str,
        create_bayes_ab_payload: dict,
        request: FixtureRequest,
    ) -> Generator:
        bayes_abs = []
        n_bayes_abs = request.param if hasattr(request, "param") else 1
        for _ in range(n_bayes_abs):
            response = client.post(
                "/bayes_ab",
                json=create_bayes_ab_payload,
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            bayes_abs.append(response.json())
        yield bayes_abs
        for bayes_ab in bayes_abs:
            client.delete(
                f"/bayes_ab/{bayes_ab['experiment_id']}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

    @mark.parametrize(
        "create_bayes_ab_payload, expected_response",
        [
            ("base_normal", 200),
            ("base_binary_normal", 200),
            ("one_arm", 422),
            ("no_notifications", 200),
            ("invalid_prior", 422),
            ("invalid_sigma", 422),
            ("invalid_params", 200),
            ("two_treatment_arms", 422),
        ],
        indirect=["create_bayes_ab_payload"],
    )
    def test_create_bayes_ab(
        self,
        create_bayes_ab_payload: dict,
        client: TestClient,
        expected_response: int,
        admin_token: str,
        clean_bayes_ab: None,
    ) -> None:
        """
        Test the creation of a Bayesian A/B test.
        """
        response = client.post(
            "/bayes_ab",
            json=create_bayes_ab_payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == expected_response

    @mark.parametrize(
        "create_bayes_abs, n_expected, create_bayes_ab_payload",
        [(1, 1, "base_normal"), (2, 2, "base_normal"), (5, 5, "base_normal")],
        indirect=["create_bayes_abs", "create_bayes_ab_payload"],
    )
    def test_get_bayes_abs(
        self,
        client: TestClient,
        n_expected: int,
        admin_token: str,
        create_bayes_abs: list,
        create_bayes_ab_payload: dict,
    ) -> None:
        """
        Test the retrieval of Bayesian A/B tests.
        """
        response = client.get(
            "/bayes_ab", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        assert len(response.json()) == n_expected

    @mark.parametrize(
        "create_bayes_abs, expected_response, create_bayes_ab_payload",
        [(1, 200, "base_normal"), (2, 200, "base_normal"), (5, 200, "base_normal")],
        indirect=["create_bayes_abs", "create_bayes_ab_payload"],
    )
    def test_draw_arm(
        self,
        client: TestClient,
        create_bayes_abs: list,
        create_bayes_ab_payload: dict,
        expected_response: int,
    ) -> None:
        id = create_bayes_abs[0]["experiment_id"]
        api_key = os.environ.get("ADMIN_API_KEY", "")
        response = client.get(
            f"/bayes_ab/{id}/draw",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert response.status_code == expected_response

    @mark.parametrize(
        "create_bayes_ab_payload, client_id, expected_response",
        [
            ("with_sticky_assignment", None, 400),
            ("with_sticky_assignment", "test_client_id", 200),
        ],
        indirect=["create_bayes_ab_payload"],
    )
    def test_draw_arm_with_client_id(
        self,
        client: TestClient,
        create_bayes_abs: list,
        create_bayes_ab_payload: dict,
        client_id: str | None,
        expected_response: int,
    ) -> None:
        id = create_bayes_abs[0]["experiment_id"]
        api_key = os.environ.get("ADMIN_API_KEY", "")
        response = client.get(
            f"/bayes_ab/{id}/draw{'?client_id=' + client_id if client_id else ''}",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert response.status_code == expected_response

    @mark.parametrize(
        "create_bayes_ab_payload", ["with_sticky_assignment"], indirect=True
    )
    def test_draw_arm_with_sticky_assignment(
        self, client: TestClient, create_bayes_abs: list, create_bayes_ab_payload: dict
    ) -> None:
        id = create_bayes_abs[0]["experiment_id"]
        api_key = os.environ.get("ADMIN_API_KEY", "")
        arm_ids = []
        for _ in range(10):
            response = client.get(
                f"/bayes_ab/{id}/draw?client_id=123",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            arm_ids.append(response.json()["arm"]["arm_id"])
        assert np.unique(arm_ids).size == 1


class TestNotifications:
    @fixture()
    def create_bayes_ab_payload(self, request: FixtureRequest) -> dict:
        payload: dict = copy.deepcopy(base_normal_payload)
        payload["arms"] = list(payload["arms"])

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
        "create_bayes_ab_payload, expected_response",
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
        indirect=["create_bayes_ab_payload"],
    )
    def test_notifications(
        self,
        client: TestClient,
        admin_token: str,
        create_bayes_ab_payload: dict,
        expected_response: int,
        clean_bayes_ab: None,
    ) -> None:
        response = client.post(
            "/bayes_ab",
            json=create_bayes_ab_payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == expected_response
