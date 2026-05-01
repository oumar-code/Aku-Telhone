"""Tests for the eSIM provisioning router (/api/v1/esim/*)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.services.ota import _profile_store

# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

PROVISION_BODY = {
    "device_id": "device-001",
    "imei": "123456789012345",
    "eid": "89049032002700000000000000000001",
    "preferred_network": "LTE",
    "plan_id": "plan-basic-001",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_store():
    """Wipe the in-memory profile store before and after each test."""
    _profile_store.clear()
    yield
    _profile_store.clear()


@pytest.fixture
async def provisioned_iccid(client: AsyncClient) -> str:
    """Provision one eSIM and return its ICCID."""
    resp = await client.post("/api/v1/esim/provision", json=PROVISION_BODY)
    assert resp.status_code == 201
    return resp.json()["iccid"]


@pytest.fixture
async def deactivated_iccid(client: AsyncClient, provisioned_iccid: str) -> str:
    """Deactivate a provisioned eSIM and return its ICCID."""
    resp = await client.delete(f"/api/v1/esim/{provisioned_iccid}")
    assert resp.status_code == 200
    return provisioned_iccid


# ---------------------------------------------------------------------------
# POST /api/v1/esim/provision
# ---------------------------------------------------------------------------


async def test_provision_returns_201(client: AsyncClient) -> None:
    response = await client.post("/api/v1/esim/provision", json=PROVISION_BODY)
    assert response.status_code == 201


async def test_provision_response_fields(client: AsyncClient) -> None:
    response = await client.post("/api/v1/esim/provision", json=PROVISION_BODY)
    data = response.json()
    assert data["status"] == "PENDING"
    assert data["eid"] == PROVISION_BODY["eid"]
    assert data["device_id"] == PROVISION_BODY["device_id"]
    assert data["plan_id"] == PROVISION_BODY["plan_id"]
    assert "iccid" in data
    assert "activation_code" in data
    assert data["activation_code"].startswith("AC$")
    assert "qr_code_url" in data


async def test_provision_invalid_imei_length(client: AsyncClient) -> None:
    body = {**PROVISION_BODY, "imei": "12345"}
    response = await client.post("/api/v1/esim/provision", json=body)
    assert response.status_code == 422


async def test_provision_non_digit_imei(client: AsyncClient) -> None:
    body = {**PROVISION_BODY, "imei": "12345678901234X"}
    response = await client.post("/api/v1/esim/provision", json=body)
    assert response.status_code == 422


async def test_provision_duplicate_eid_still_succeeds(client: AsyncClient) -> None:
    resp1 = await client.post("/api/v1/esim/provision", json=PROVISION_BODY)
    resp2 = await client.post("/api/v1/esim/provision", json=PROVISION_BODY)
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp1.json()["iccid"] == resp2.json()["iccid"]


async def test_provision_service_error_returns_502(client: AsyncClient) -> None:
    with patch("app.routers.esim.esim_service.provision", side_effect=RuntimeError("boom")):
        response = await client.post("/api/v1/esim/provision", json=PROVISION_BODY)
    assert response.status_code == 502


# ---------------------------------------------------------------------------
# GET /api/v1/esim/{iccid}
# ---------------------------------------------------------------------------


async def test_get_profile_returns_200(
    client: AsyncClient, provisioned_iccid: str
) -> None:
    response = await client.get(f"/api/v1/esim/{provisioned_iccid}")
    assert response.status_code == 200
    data = response.json()
    assert data["iccid"] == provisioned_iccid
    assert data["status"] == "PENDING"


async def test_get_profile_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/esim/nonexistent-iccid")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/v1/esim/{iccid}/switch-network
# ---------------------------------------------------------------------------


async def test_switch_network_returns_202(
    client: AsyncClient, provisioned_iccid: str
) -> None:
    body = {"target_network": "5G"}
    with patch("app.routers.esim.asyncio.create_task"):
        response = await client.patch(
            f"/api/v1/esim/{provisioned_iccid}/switch-network", json=body
        )
    assert response.status_code == 202
    data = response.json()
    assert data["iccid"] == provisioned_iccid
    assert data["status"] == "SWITCHING"
    assert "task_id" in data


async def test_switch_network_not_found(client: AsyncClient) -> None:
    body = {"target_network": "LTE"}
    response = await client.patch("/api/v1/esim/nonexistent/switch-network", json=body)
    assert response.status_code == 404


async def test_switch_network_deactivated_returns_409(
    client: AsyncClient, deactivated_iccid: str
) -> None:
    body = {"target_network": "LTE"}
    response = await client.patch(
        f"/api/v1/esim/{deactivated_iccid}/switch-network", json=body
    )
    assert response.status_code == 409


# ---------------------------------------------------------------------------
# DELETE /api/v1/esim/{iccid}
# ---------------------------------------------------------------------------


async def test_deactivate_returns_200(
    client: AsyncClient, provisioned_iccid: str
) -> None:
    response = await client.delete(f"/api/v1/esim/{provisioned_iccid}")
    assert response.status_code == 200
    data = response.json()
    assert data["iccid"] == provisioned_iccid
    assert data["status"] == "DEACTIVATED"


async def test_deactivate_not_found(client: AsyncClient) -> None:
    response = await client.delete("/api/v1/esim/nonexistent")
    assert response.status_code == 404


async def test_deactivate_already_deactivated_returns_409(
    client: AsyncClient, deactivated_iccid: str
) -> None:
    response = await client.delete(f"/api/v1/esim/{deactivated_iccid}")
    assert response.status_code == 409


# ---------------------------------------------------------------------------
# POST /api/v1/esim/{iccid}/ota-push
# ---------------------------------------------------------------------------


async def test_ota_push_returns_202(
    client: AsyncClient, provisioned_iccid: str
) -> None:
    body = {"payload_type": "PROFILE_UPDATE", "payload": {}, "priority": 5}
    with patch("app.routers.esim.asyncio.create_task"):
        response = await client.post(
            f"/api/v1/esim/{provisioned_iccid}/ota-push", json=body
        )
    assert response.status_code == 202
    data = response.json()
    assert data["iccid"] == provisioned_iccid
    assert data["status"] == "QUEUED"
    assert "task_id" in data


async def test_ota_push_not_found(client: AsyncClient) -> None:
    body = {"payload_type": "PROFILE_UPDATE"}
    response = await client.post("/api/v1/esim/nonexistent/ota-push", json=body)
    assert response.status_code == 404


async def test_ota_push_deactivated_returns_409(
    client: AsyncClient, deactivated_iccid: str
) -> None:
    body = {"payload_type": "PROFILE_UPDATE"}
    with patch("app.routers.esim.asyncio.create_task"):
        response = await client.post(
            f"/api/v1/esim/{deactivated_iccid}/ota-push", json=body
        )
    assert response.status_code == 409
