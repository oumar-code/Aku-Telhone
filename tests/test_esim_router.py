"""Integration tests for the eSIM provisioning router."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.services.ota import _profile_store, _task_registry

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_stores():
    """Clear in-process stores before and after every test."""
    _profile_store.clear()
    _task_registry.clear()
    yield
    _profile_store.clear()
    _task_registry.clear()


_PROVISION_PAYLOAD = {
    "device_id": "dev-router-1",
    "imei": "123456789012345",
    "eid": "eid-router-1",
    "plan_id": "plan-test",
    "preferred_network": "LTE",
}


async def _provision(client: AsyncClient) -> str:
    """Provision a profile and return the ICCID."""
    resp = await client.post("/api/v1/esim/provision", json=_PROVISION_PAYLOAD)
    assert resp.status_code == 201
    return resp.json()["iccid"]


# ---------------------------------------------------------------------------
# POST /api/v1/esim/provision
# ---------------------------------------------------------------------------


async def test_provision_success(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/esim/provision", json=_PROVISION_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "PENDING"
    assert data["iccid"].startswith("89234")
    assert data["activation_code"].startswith("AC$")


# ---------------------------------------------------------------------------
# GET /api/v1/esim/{iccid}
# ---------------------------------------------------------------------------


async def test_get_profile_not_found(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/esim/no-such-iccid")
    assert resp.status_code == 404


async def test_get_profile_found(client: AsyncClient) -> None:
    iccid = await _provision(client)
    resp = await client.get(f"/api/v1/esim/{iccid}")
    assert resp.status_code == 200
    assert resp.json()["iccid"] == iccid


# ---------------------------------------------------------------------------
# PATCH /api/v1/esim/{iccid}/switch-network
# ---------------------------------------------------------------------------


async def test_switch_network_not_found(client: AsyncClient) -> None:
    resp = await client.patch(
        "/api/v1/esim/ghost-iccid/switch-network",
        json={"target_network": "LTE"},
    )
    assert resp.status_code == 404


async def test_switch_network_success(client: AsyncClient) -> None:
    iccid = await _provision(client)
    resp = await client.patch(
        f"/api/v1/esim/{iccid}/switch-network",
        json={"target_network": "5G"},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "SWITCHING"
    assert "task_id" in data


async def test_switch_network_deactivated_returns_409(client: AsyncClient) -> None:
    iccid = await _provision(client)
    await client.delete(f"/api/v1/esim/{iccid}")
    resp = await client.patch(
        f"/api/v1/esim/{iccid}/switch-network",
        json={"target_network": "LTE"},
    )
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# DELETE /api/v1/esim/{iccid}
# ---------------------------------------------------------------------------


async def test_deactivate_success(client: AsyncClient) -> None:
    iccid = await _provision(client)
    resp = await client.delete(f"/api/v1/esim/{iccid}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "DEACTIVATED"


async def test_deactivate_not_found(client: AsyncClient) -> None:
    resp = await client.delete("/api/v1/esim/no-iccid")
    assert resp.status_code == 404


async def test_deactivate_already_deactivated_returns_409(client: AsyncClient) -> None:
    iccid = await _provision(client)
    await client.delete(f"/api/v1/esim/{iccid}")
    resp = await client.delete(f"/api/v1/esim/{iccid}")
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# POST /api/v1/esim/{iccid}/ota-push
# ---------------------------------------------------------------------------


_OTA_BODY = {"payload_type": "PROFILE_UPDATE", "payload": {}, "priority": 5}


async def test_ota_push_not_found(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/esim/ghost-iccid/ota-push", json=_OTA_BODY)
    assert resp.status_code == 404


async def test_ota_push_deactivated_returns_409(client: AsyncClient) -> None:
    iccid = await _provision(client)
    await client.delete(f"/api/v1/esim/{iccid}")
    resp = await client.post(f"/api/v1/esim/{iccid}/ota-push", json=_OTA_BODY)
    assert resp.status_code == 409


async def test_ota_push_success(client: AsyncClient) -> None:
    iccid = await _provision(client)
    resp = await client.post(f"/api/v1/esim/{iccid}/ota-push", json=_OTA_BODY)
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "QUEUED"
    assert "task_id" in data
