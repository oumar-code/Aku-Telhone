"""Tests for the device attestation router (/api/v1/devices/*)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

DEVICE_ID = "device-attest-001"

ATTEST_BODY = {
    "device_id": DEVICE_ID,
    "attestation_token": "token-android-abc123",
    "platform": "android",
    "firmware_hash": "abc123def456",
}


def _make_mock_async_client(post_side_effect=None, post_return=None):
    """Return a mock httpx.AsyncClient usable as an async context manager."""
    mock = AsyncMock()
    mock.__aenter__.return_value = mock
    mock.__aexit__.return_value = None
    if post_side_effect is not None:
        mock.post.side_effect = post_side_effect
    elif post_return is not None:
        mock.post.return_value = post_return
    return mock


# ---------------------------------------------------------------------------
# POST /api/v1/devices/{device_id}/attest
# ---------------------------------------------------------------------------


async def test_attest_device_success(client: AsyncClient) -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "attested": True,
        "trust_level": "FULL",
        "reason": None,
        "ref": "ighub-ref-001",
    }
    mock_client = _make_mock_async_client(post_return=mock_response)

    with patch("app.routers.devices.httpx.AsyncClient", return_value=mock_client):
        response = await client.post(
            f"/api/v1/devices/{DEVICE_ID}/attest",
            json=ATTEST_BODY,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == DEVICE_ID
    assert data["attested"] is True
    assert data["trust_level"] == "FULL"
    assert data["ighub_ref"] == "ighub-ref-001"


async def test_attest_device_without_firmware_hash(client: AsyncClient) -> None:
    body = {k: v for k, v in ATTEST_BODY.items() if k != "firmware_hash"}
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "attested": True,
        "trust_level": "LIMITED",
        "reason": None,
        "ref": None,
        "ighub_ref": "ighub-ref-002",
    }
    mock_client = _make_mock_async_client(post_return=mock_response)

    with patch("app.routers.devices.httpx.AsyncClient", return_value=mock_client):
        response = await client.post(f"/api/v1/devices/{DEVICE_ID}/attest", json=body)

    assert response.status_code == 200
    data = response.json()
    assert data["trust_level"] == "LIMITED"
    assert data["ighub_ref"] == "ighub-ref-002"


async def test_attest_device_id_mismatch_returns_422(client: AsyncClient) -> None:
    body = {**ATTEST_BODY, "device_id": "different-device"}
    response = await client.post(f"/api/v1/devices/{DEVICE_ID}/attest", json=body)
    assert response.status_code == 422


async def test_attest_device_ighub_http_error_returns_502(
    client: AsyncClient,
) -> None:
    mock_http_response = MagicMock()
    mock_http_response.status_code = 403
    mock_http_response.text = "Forbidden"
    error = httpx.HTTPStatusError(
        "403 Forbidden",
        request=MagicMock(),
        response=mock_http_response,
    )
    mock_client = _make_mock_async_client(post_side_effect=error)

    with patch("app.routers.devices.httpx.AsyncClient", return_value=mock_client):
        response = await client.post(
            f"/api/v1/devices/{DEVICE_ID}/attest", json=ATTEST_BODY
        )

    assert response.status_code == 502


async def test_attest_device_ighub_unreachable_returns_503(
    client: AsyncClient,
) -> None:
    error = httpx.RequestError("Connection refused", request=MagicMock())
    mock_client = _make_mock_async_client(post_side_effect=error)

    with patch("app.routers.devices.httpx.AsyncClient", return_value=mock_client):
        response = await client.post(
            f"/api/v1/devices/{DEVICE_ID}/attest", json=ATTEST_BODY
        )

    assert response.status_code == 503
