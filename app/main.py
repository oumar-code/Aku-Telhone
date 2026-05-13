"""Aku-Telhone FastAPI application factory — eSIM provisioning service."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import app_api, customers, devices, esim, platform, sims


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown hook — initialise MVNO client here if needed."""
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Aku-Telhone",
        description=(
            "Connectivity orchestration platform for the Aku ecosystem. Handles eSIM and "
            "physical SIM lifecycle management, customer onboarding, app-facing activation "
            "flows, hub policy integration, observability, and device attestation via "
            "Aku-IGHub."
        ),
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.allowed_origins.split(",") if origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(esim.router)
    app.include_router(devices.router)
    app.include_router(customers.router)
    app.include_router(sims.router)
    app.include_router(app_api.router)
    app.include_router(platform.router)

    @app.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "Aku-Telhone",
            "scope": "connectivity-platform",
        }

    return app


app = create_app()
