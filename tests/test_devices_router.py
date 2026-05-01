"""Tests for the device attestation router."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# POST /api/v1/devices/{device_id}/attest
# ---------------------------------------------------------------------------


async def test_attest_device_id_mismatch(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/devices/device-A/attest",
        json={
            "device_id": "device-B",  # intentional mismatch
            "attestation_token": "tok",
            "platform": "android",
        },
    )
    assert resp.status_code == 422


async def test_attest_device_success(client: AsyncClient) -> None:
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "attested": True,
        "trust_level": "FULL",
        "reason": None,
        "ref": "ighub-ref-001",
    }

    mock_http_client = AsyncMock()
    mock_http_client.post = AsyncMock(return_value=mock_resp)
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.routers.devices.httpx.AsyncClient", return_value=mock_http_client):
        resp = await client.post(
            "/api/v1/devices/dev-1/attest",
            json={
                "device_id": "dev-1",
                "attestation_token": "tok",
                "platform": "android",
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["attested"] is True
    assert data["trust_level"] == "FULL"
    assert data["ighub_ref"] == "ighub-ref-001"


async def test_attest_device_ighub_http_error(client: AsyncClient) -> None:
    request = httpx.Request("POST", "http://ighub/attest")
    error_response = httpx.Response(503, request=request, text="service unavailable")
    http_exc = httpx.HTTPStatusError("503", request=request, response=error_response)

    mock_http_client = AsyncMock()
    mock_http_client.post = AsyncMock(side_effect=http_exc)
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.routers.devices.httpx.AsyncClient", return_value=mock_http_client):
        resp = await client.post(
            "/api/v1/devices/dev-2/attest",
            json={
                "device_id": "dev-2",
                "attestation_token": "tok",
                "platform": "ios",
            },
        )

    assert resp.status_code == 502


async def test_attest_device_ighub_unreachable(client: AsyncClient) -> None:
    request = httpx.Request("POST", "http://ighub/attest")
    net_exc = httpx.ConnectError("connection refused", request=request)

    mock_http_client = AsyncMock()
    mock_http_client.post = AsyncMock(side_effect=net_exc)
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.routers.devices.httpx.AsyncClient", return_value=mock_http_client):
        resp = await client.post(
            "/api/v1/devices/dev-3/attest",
            json={
                "device_id": "dev-3",
                "attestation_token": "tok",
                "platform": "embedded",
            },
        )

    assert resp.status_code == 503
