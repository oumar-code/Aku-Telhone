"""Integration tests for the Nigeria-market connectivity platform APIs."""

from __future__ import annotations

import asyncio

import httpx
import pytest
from httpx import AsyncClient

from app.services.ota import ota_service


@pytest.fixture(autouse=True)
def fast_ota_delivery() -> None:
    ota_service._OTA_SIMULATED_DELAY = 0


async def _create_customer(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/customers/onboard",
        json={
            "full_name": "Amina Musa",
            "email": "amina@example.com",
            "phone_number": "+2348012345678",
            "nin_reference": "nin-ref-001",
            "role": "STUDENT",
            "allowed_bundles": ["edu-daily", "voice-starter"],
            "metadata": {"state": "Kaduna"},
        },
    )
    assert response.status_code == 201
    return response.json()


async def test_customer_onboarding_and_app_dashboard(client: AsyncClient) -> None:
    customer = await _create_customer(client)

    session_response = await client.post(
        "/api/v1/app/sessions",
        json={
            "customer_id": customer["customer_id"],
            "channel": "mobile",
            "device_id": "android-001",
        },
    )
    assert session_response.status_code == 201
    assert session_response.json()["customer_id"] == customer["customer_id"]

    dashboard_response = await client.get(
        f"/api/v1/app/customers/{customer['customer_id']}/dashboard"
    )
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert dashboard["customer"]["kyc_status"] == "VERIFIED"
    assert dashboard["available_bundles"][0]["bundle_id"] == "edu-daily"


async def test_physical_sim_inventory_assignment_activation_and_subscription(
    client: AsyncClient,
) -> None:
    customer = await _create_customer(client)

    inventory_response = await client.post(
        "/api/v1/sims/inventory",
        json={
            "iccid": "8923400000000000001",
            "serial_number": "SIM-NG-0001",
            "msisdn": "+2349010000001",
            "plan_id": "ng-starter",
            "preferred_network": "LTE",
            "edge_id": "edge-kd-01",
        },
    )
    assert inventory_response.status_code == 201
    assert inventory_response.json()["status"] == "INVENTORIED"

    assign_response = await client.post(
        "/api/v1/sims/8923400000000000001/assign",
        json={
            "customer_id": customer["customer_id"],
            "device_id": "tecno-physical-01",
            "allowed_bundles": ["edu-daily"],
        },
    )
    assert assign_response.status_code == 200
    assigned = assign_response.json()
    assert assigned["status"] == "ASSIGNED"
    assert assigned["subscription_id"].startswith("sub-")

    activate_response = await client.post("/api/v1/sims/8923400000000000001/activate")
    assert activate_response.status_code == 200
    assert activate_response.json()["status"] == "ACTIVE"

    subscription_response = await client.get(f"/api/v1/subscriptions/{assigned['subscription_id']}")
    assert subscription_response.status_code == 200
    subscription = subscription_response.json()
    assert subscription["form_factor"] == "PHYSICAL"
    assert subscription["status"] == "ACTIVE"

    activation_status_response = await client.get(
        f"/api/v1/app/subscriptions/{assigned['subscription_id']}/activation"
    )
    assert activation_status_response.status_code == 200
    assert activation_status_response.json()["ready_for_use"] is True


async def test_physical_sim_replace_and_deactivate(client: AsyncClient) -> None:
    customer = await _create_customer(client)

    for suffix in ("11", "12"):
        response = await client.post(
            "/api/v1/sims/inventory",
            json={
                "iccid": f"89234000000000000{suffix}",
                "serial_number": f"SIM-NG-00{suffix}",
                "plan_id": "teacher-plus",
                "preferred_network": "5G",
            },
        )
        assert response.status_code == 201

    assign_response = await client.post(
        "/api/v1/sims/8923400000000000011/assign",
        json={
            "customer_id": customer["customer_id"],
            "activate_immediately": True,
        },
    )
    subscription_id = assign_response.json()["subscription_id"]

    replace_response = await client.post(
        "/api/v1/sims/8923400000000000011/replace",
        json={
            "replacement_iccid": "8923400000000000012",
            "reason": "Lost SIM during inter-state travel",
        },
    )
    assert replace_response.status_code == 200
    replaced = replace_response.json()
    assert replaced["iccid"] == "8923400000000000012"
    assert replaced["subscription_id"] == subscription_id

    deactivate_response = await client.delete("/api/v1/sims/8923400000000000012")
    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["status"] == "DEACTIVATED"


async def test_esim_provisioning_creates_unified_subscription_and_activation_status(
    client: AsyncClient,
) -> None:
    customer = await _create_customer(client)

    response = await client.post(
        "/api/v1/esim/provision",
        json={
            "device_id": "iphone-15-pro",
            "imei": "123456789012345",
            "eid": "89049032000000000000000000000001",
            "plan_id": "esim-premium",
            "customer_id": customer["customer_id"],
            "preferred_network": "LTE",
        },
    )
    assert response.status_code == 201
    provisioned = response.json()
    assert provisioned["subscription_id"].startswith("sub-")
    assert provisioned["qr_code_url"].endswith(".png")

    profile_response = await client.get(f"/api/v1/esim/{provisioned['iccid']}")
    assert profile_response.status_code == 200
    assert profile_response.json()["subscription_id"] == provisioned["subscription_id"]

    activation_response = await client.get(
        f"/api/v1/app/subscriptions/{provisioned['subscription_id']}/activation"
    )
    assert activation_response.status_code == 200
    activation = activation_response.json()
    assert activation["subscription"]["form_factor"] == "ESIM"
    assert activation["next_step"].startswith("Scan QR code")


async def test_esim_ota_operations_update_subscription_state(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/esim/provision",
        json={
            "device_id": "pixel-9",
            "imei": "543210987654321",
            "eid": "89049032000000000000000000000002",
            "plan_id": "esim-starter",
        },
    )
    provisioned = response.json()

    switch_response = await client.patch(
        f"/api/v1/esim/{provisioned['iccid']}/switch-network",
        json={"target_network": "5G", "target_plan_id": "esim-plus"},
    )
    assert switch_response.status_code == 202
    await asyncio.sleep(0)

    push_response = await client.post(
        f"/api/v1/esim/{provisioned['iccid']}/ota-push",
        json={"payload_type": "PROFILE_UPDATE", "payload": {"refresh": True}, "priority": 8},
    )
    assert push_response.status_code == 202
    await asyncio.sleep(0)

    subscription_response = await client.get(
        f"/api/v1/subscriptions/{provisioned['subscription_id']}"
    )
    assert subscription_response.status_code == 200
    subscription = subscription_response.json()
    assert subscription["preferred_network"] == "5G"
    assert subscription["plan_id"] == "esim-plus"


async def test_hub_policy_metrics_and_readiness_endpoints(client: AsyncClient) -> None:
    policy_response = await client.post(
        "/api/v1/platform/hub-policy-sync",
        json={
            "edge_id": "edge-lag-01",
            "super_hub_id": "super-lag",
            "education_qos_priority": True,
            "top_cached_assets": ["math/video-01.mp4", "waec/mock-02.pdf"],
            "preferred_call_route": "LOCAL_EDGE",
            "allowed_bundles": ["edu-daily"],
        },
    )
    assert policy_response.status_code == 202

    integration_response = await client.get("/api/v1/platform/integration-contracts")
    assert integration_response.status_code == 200
    assert "edge_hub" in integration_response.json()["responsibilities"]

    readiness_response = await client.get("/readyz")
    assert readiness_response.status_code == 200
    assert readiness_response.json()["status"] == "ready"

    metrics_snapshot_response = await client.get("/api/v1/platform/metrics")
    assert metrics_snapshot_response.status_code == 200
    assert metrics_snapshot_response.json()["hub_policies_total"] == 1

    metrics_response = await client.get("/metrics")
    assert metrics_response.status_code == 200
    assert "aku_hub_policies_total 1" in metrics_response.text


async def test_device_attestation_success_and_validation_errors(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeIGHubClient:
        def __init__(self, *args, **kwargs) -> None:
            del args, kwargs

        async def __aenter__(self) -> FakeIGHubClient:
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            del exc_type, exc, tb

        async def post(self, path: str, json: dict) -> httpx.Response:
            assert path == "/api/v1/devices/attest"
            assert json["requester_service"] == "aku-telhone"
            return httpx.Response(
                status_code=200,
                json={"attested": True, "trust_level": "FULL", "ighub_ref": "igh-123"},
            )

    monkeypatch.setattr("app.routers.devices.httpx.AsyncClient", FakeIGHubClient)

    response = await client.post(
        "/api/v1/devices/device-01/attest",
        json={
            "device_id": "device-01",
            "attestation_token": "token-abc",
            "platform": "android",
        },
    )
    assert response.status_code == 200
    assert response.json()["trust_level"] == "FULL"

    mismatch_response = await client.post(
        "/api/v1/devices/device-01/attest",
        json={
            "device_id": "device-02",
            "attestation_token": "token-abc",
            "platform": "android",
        },
    )
    assert mismatch_response.status_code == 422


async def test_device_attestation_unreachable_ighub(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class UnreachableIGHubClient:
        def __init__(self, *args, **kwargs) -> None:
            del args, kwargs

        async def __aenter__(self) -> UnreachableIGHubClient:
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            del exc_type, exc, tb

        async def post(self, path: str, json: dict) -> httpx.Response:
            del path, json
            raise httpx.RequestError("network down", request=httpx.Request("POST", "http://ighub"))

    monkeypatch.setattr("app.routers.devices.httpx.AsyncClient", UnreachableIGHubClient)

    response = await client.post(
        "/api/v1/devices/device-01/attest",
        json={
            "device_id": "device-01",
            "attestation_token": "token-abc",
            "platform": "android",
        },
    )
    assert response.status_code == 503


async def test_error_paths_for_customer_sim_and_subscription_apis(client: AsyncClient) -> None:
    missing_customer = await client.get("/api/v1/customers/cust-missing")
    assert missing_customer.status_code == 404

    missing_sim = await client.post(
        "/api/v1/sims/8923400999999999999/assign",
        json={"customer_id": "cust-missing"},
    )
    assert missing_sim.status_code == 404

    missing_subscription = await client.get("/api/v1/app/subscriptions/sub-missing/activation")
    assert missing_subscription.status_code == 404
