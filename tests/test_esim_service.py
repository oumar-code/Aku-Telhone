"""Unit tests for app.services.esim — ESIMService and helpers."""

from __future__ import annotations

import pytest

from app.schemas.esim import ESIMProvisionRequest, ESIMStatus, NetworkTechnology
from app.services.esim import (
    _generate_activation_code,
    _generate_iccid,
    _qr_code_url,
    esim_service,
)
from app.services.ota import _profile_store, _task_registry

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_stores():
    """Wipe the in-process stores before and after every test."""
    _profile_store.clear()
    _task_registry.clear()
    yield
    _profile_store.clear()
    _task_registry.clear()


_BASE_REQUEST = dict(
    device_id="dev-1",
    imei="123456789012345",
    eid="eid-001",
    plan_id="plan-basic",
    preferred_network=NetworkTechnology.LTE,
)


def _make_request(**overrides) -> ESIMProvisionRequest:
    return ESIMProvisionRequest(**{**_BASE_REQUEST, **overrides})


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def test_generate_iccid_format():
    iccid = _generate_iccid("test-eid")
    assert iccid.startswith("89234")
    assert iccid.isdigit()


def test_generate_iccid_deterministic():
    assert _generate_iccid("same-eid") == _generate_iccid("same-eid")


def test_generate_iccid_different_for_different_eids():
    assert _generate_iccid("eid-a") != _generate_iccid("eid-b")


def test_generate_activation_code_prefix():
    code = _generate_activation_code("89234abc")
    assert code.startswith("AC$")


def test_qr_code_url_contains_iccid():
    url = _qr_code_url("iccid-123", "AC$TOKEN")
    assert "iccid-123" in url


# ---------------------------------------------------------------------------
# ESIMService.provision
# ---------------------------------------------------------------------------


async def test_provision_returns_pending_status():
    resp = await esim_service.provision(_make_request())
    assert resp.status == ESIMStatus.PENDING


async def test_provision_iccid_format():
    resp = await esim_service.provision(_make_request())
    assert resp.iccid.startswith("89234")


async def test_provision_activation_code_prefix():
    resp = await esim_service.provision(_make_request())
    assert resp.activation_code.startswith("AC$")


async def test_provision_stores_profile():
    resp = await esim_service.provision(_make_request())
    assert resp.iccid in _profile_store


async def test_provision_duplicate_eid_does_not_raise():
    req = _make_request(eid="eid-dup")
    await esim_service.provision(req)
    await esim_service.provision(req)  # second call must not raise


# ---------------------------------------------------------------------------
# ESIMService.get_profile
# ---------------------------------------------------------------------------


async def test_get_profile_not_found():
    with pytest.raises(KeyError):
        await esim_service.get_profile("no-such-iccid")


async def test_get_profile_found():
    prov = await esim_service.provision(_make_request(eid="eid-get"))
    profile = await esim_service.get_profile(prov.iccid)
    assert profile.iccid == prov.iccid
    assert profile.status == ESIMStatus.PENDING


# ---------------------------------------------------------------------------
# ESIMService.is_deactivated
# ---------------------------------------------------------------------------


async def test_is_deactivated_false_for_pending():
    prov = await esim_service.provision(_make_request(eid="eid-active"))
    assert not await esim_service.is_deactivated(prov.iccid)


async def test_is_deactivated_false_for_unknown_iccid():
    assert not await esim_service.is_deactivated("unknown-iccid")


# ---------------------------------------------------------------------------
# ESIMService.deactivate
# ---------------------------------------------------------------------------


async def test_deactivate_success():
    prov = await esim_service.provision(_make_request(eid="eid-deact"))
    result = await esim_service.deactivate(prov.iccid)
    assert result.status == ESIMStatus.DEACTIVATED
    assert await esim_service.is_deactivated(prov.iccid)


async def test_deactivate_not_found():
    with pytest.raises(KeyError):
        await esim_service.deactivate("ghost-iccid")


async def test_deactivate_already_deactivated_raises_value_error():
    prov = await esim_service.provision(_make_request(eid="eid-deact2"))
    await esim_service.deactivate(prov.iccid)
    with pytest.raises(ValueError, match="already deactivated"):
        await esim_service.deactivate(prov.iccid)
