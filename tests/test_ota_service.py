"""Unit tests for app.services.ota — OTAService and helper functions."""

from __future__ import annotations

from unittest.mock import patch

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
    """Reset in-memory stores before and after each test."""
    _profile_store.clear()
    _task_registry.clear()
    yield
    _profile_store.clear()
    _task_registry.clear()


# ---------------------------------------------------------------------------
# Helper / utility function tests
# ---------------------------------------------------------------------------


def test_new_task_id_format():
    task_id = new_task_id()
    assert task_id.startswith("ota-")


def test_new_task_id_unique():
    assert new_task_id() != new_task_id()


def test_upsert_profile_creates_entry():
    _upsert_profile("iccid-001", status="PENDING", eid="eid-001")
    assert _profile_store["iccid-001"]["status"] == "PENDING"
    assert _profile_store["iccid-001"]["eid"] == "eid-001"


def test_upsert_profile_merges_existing():
    _upsert_profile("iccid-001", status="PENDING")
    _upsert_profile("iccid-001", status="ACTIVE")
    assert _profile_store["iccid-001"]["status"] == "ACTIVE"


def test_get_profile_returns_record():
    _upsert_profile("iccid-002", status="ACTIVE")
    record = get_profile("iccid-002")
    assert record is not None
    assert record["status"] == "ACTIVE"


def test_get_profile_returns_none_for_missing():
    assert get_profile("does-not-exist") is None


def test_get_task_status_returns_record():
    _task_registry["task-001"] = {"status": "IN_PROGRESS"}
    assert get_task_status("task-001") == {"status": "IN_PROGRESS"}


def test_get_task_status_returns_none_for_missing():
    assert get_task_status("no-such-task") is None


# ---------------------------------------------------------------------------
# OTAService.push_profile
# ---------------------------------------------------------------------------


async def test_push_profile_completes_and_updates_store():
    svc = OTAService()
    _upsert_profile("iccid-push", status="PENDING")

    with patch.object(svc, "_OTA_SIMULATED_DELAY", 0):
        await svc.push_profile(iccid="iccid-push", task_id="task-push-001")

    assert _task_registry["task-push-001"]["status"] == "COMPLETED"
    assert _profile_store["iccid-push"]["status"] == "ACTIVE"
    assert _profile_store["iccid-push"]["last_ota_push_at"] is not None


async def test_push_profile_handles_exception():
    svc = OTAService()

    async def _fail(*args, **kwargs):
        raise RuntimeError("simulated OTA failure")

    with patch("app.services.ota.asyncio.sleep", side_effect=_fail):
        await svc.push_profile(iccid="iccid-fail", task_id="task-push-fail")

    assert _task_registry["task-push-fail"]["status"] == "FAILED"
    assert _task_registry["task-push-fail"]["error"] == "simulated OTA failure"


# ---------------------------------------------------------------------------
# OTAService.switch_network
# ---------------------------------------------------------------------------


async def test_switch_network_completes_and_updates_store():
    svc = OTAService()
    _upsert_profile("iccid-switch", status="ACTIVE")

    with patch.object(svc, "_OTA_SIMULATED_DELAY", 0):
        await svc.switch_network(
            iccid="iccid-switch",
            task_id="task-switch-001",
            target_network="5G",
            target_plan_id="plan-5g",
        )

    assert _task_registry["task-switch-001"]["status"] == "COMPLETED"
    assert _profile_store["iccid-switch"]["status"] == "ACTIVE"
    assert _profile_store["iccid-switch"]["preferred_network"] == "5G"
    assert _profile_store["iccid-switch"]["plan_id"] == "plan-5g"


async def test_switch_network_without_plan_id():
    svc = OTAService()
    _upsert_profile("iccid-sw2", status="ACTIVE")

    with patch.object(svc, "_OTA_SIMULATED_DELAY", 0):
        await svc.switch_network(
            iccid="iccid-sw2",
            task_id="task-switch-002",
            target_network="LTE-M",
        )

    assert _task_registry["task-switch-002"]["status"] == "COMPLETED"
    assert _profile_store["iccid-sw2"]["preferred_network"] == "LTE-M"
    assert "plan_id" not in _profile_store["iccid-sw2"]


async def test_switch_network_handles_exception():
    svc = OTAService()

    async def _fail(*args, **kwargs):
        raise RuntimeError("simulated switch failure")

    with patch("app.services.ota.asyncio.sleep", side_effect=_fail):
        await svc.switch_network(
            iccid="iccid-sw-fail",
            task_id="task-switch-fail",
            target_network="NB-IoT",
        )

    assert _task_registry["task-switch-fail"]["status"] == "FAILED"
    assert _profile_store["iccid-sw-fail"]["status"] == "ACTIVE"
