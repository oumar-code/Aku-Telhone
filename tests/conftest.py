"""Pytest configuration and shared fixtures for Aku-Telhone tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.ota import _profile_store, _task_registry
from app.services.platform import (
    _app_session_store,
    _audit_log,
    _customer_store,
    _hub_policy_store,
    _physical_sim_store,
    _subscription_store,
)


@pytest.fixture(autouse=True)
def reset_in_memory_stores() -> None:
    _profile_store.clear()
    _task_registry.clear()
    _customer_store.clear()
    _subscription_store.clear()
    _physical_sim_store.clear()
    _app_session_store.clear()
    _hub_policy_store.clear()
    _audit_log.clear()


@pytest.fixture
async def client() -> AsyncClient:
    """Async HTTP test client bound to the Aku-Telhone ASGI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
