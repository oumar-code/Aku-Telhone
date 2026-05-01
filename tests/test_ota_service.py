"""Unit tests for OTA service helper functions and OTAService."""

from __future__ import annotations

import pytest

from app.services.ota import (
    OTAService,
    _profile_store,
    _task_registry,
    _upsert_profile,
    get_profile,
    get_task_status,
    new_task_id,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_stores():
    _profile_store.clear()
    _task_registry.clear()
    yield
    _profile_store.clear()
    _task_registry.clear()


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def test_new_task_id_has_ota_prefix():
    assert new_task_id().startswith("ota-")


def test_new_task_id_is_unique():
    assert new_task_id() != new_task_id()


def test_get_task_status_missing_returns_none():
    assert get_task_status("nonexistent") is None


def test_get_task_status_present():
    _task_registry["tid-1"] = {"status": "COMPLETED"}
    assert get_task_status("tid-1")["status"] == "COMPLETED"


def test_upsert_profile_creates_new_entry():
    _upsert_profile("iccid-x", status="PENDING", eid="eid-x")
    assert _profile_store["iccid-x"]["status"] == "PENDING"
    assert _profile_store["iccid-x"]["eid"] == "eid-x"


def test_upsert_profile_merges_updates():
    _upsert_profile("iccid-y", status="PENDING")
    _upsert_profile("iccid-y", status="ACTIVE")
    assert _profile_store["iccid-y"]["status"] == "ACTIVE"


def test_get_profile_missing_returns_none():
    assert get_profile("missing") is None


def test_get_profile_present():
    _upsert_profile("iccid-z", status="ACTIVE")
    assert get_profile("iccid-z")["status"] == "ACTIVE"


# ---------------------------------------------------------------------------
# OTAService.push_profile
# ---------------------------------------------------------------------------


async def test_push_profile_completes():
    svc = OTAService()
    svc._OTA_SIMULATED_DELAY = 0.0
    await svc.push_profile(iccid="iccid-ota", task_id="task-push")
    assert _task_registry["task-push"]["status"] == "COMPLETED"
    assert _profile_store["iccid-ota"]["status"] == "ACTIVE"


async def test_push_profile_records_payload_type():
    svc = OTAService()
    svc._OTA_SIMULATED_DELAY = 0.0
    await svc.push_profile(
        iccid="iccid-p2", task_id="task-p2", payload_type="CONFIG_DELTA", priority=9
    )
    record = _task_registry["task-p2"]
    assert record["payload_type"] == "CONFIG_DELTA"
    assert record["priority"] == 9


# ---------------------------------------------------------------------------
# OTAService.switch_network
# ---------------------------------------------------------------------------


async def test_switch_network_completes():
    svc = OTAService()
    svc._OTA_SIMULATED_DELAY = 0.0
    await svc.switch_network(
        iccid="iccid-sw",
        task_id="task-sw",
        target_network="5G",
        target_plan_id="plan-new",
    )
    assert _task_registry["task-sw"]["status"] == "COMPLETED"
    assert _profile_store["iccid-sw"]["status"] == "ACTIVE"
    assert _profile_store["iccid-sw"]["preferred_network"] == "5G"
    assert _profile_store["iccid-sw"]["plan_id"] == "plan-new"


async def test_switch_network_without_plan_id():
    svc = OTAService()
    svc._OTA_SIMULATED_DELAY = 0.0
    await svc.switch_network(
        iccid="iccid-sw2",
        task_id="task-sw2",
        target_network="LTE-M",
    )
    assert _task_registry["task-sw2"]["status"] == "COMPLETED"
    assert "plan_id" not in _profile_store.get("iccid-sw2", {})
