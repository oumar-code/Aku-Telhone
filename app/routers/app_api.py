"""Consumer application APIs for Aku-Telhone clients."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas.connectivity import (
    ActivationStatusResponse,
    AppSessionRequest,
    AppSessionResponse,
    LineStatusResponse,
)
from app.services.platform import platform_service

router = APIRouter(prefix="/api/v1/app", tags=["app"])


@router.post(
    "/sessions",
    response_model=AppSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an Aku-Telhone app session",
)
async def create_app_session(body: AppSessionRequest) -> AppSessionResponse:
    try:
        return platform_service.create_app_session(body)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer '{exc.args[0]}' not found",
        ) from exc


@router.get(
    "/customers/{customer_id}/dashboard",
    response_model=LineStatusResponse,
    summary="Get customer dashboard data for the Aku-Telhone app",
)
async def get_dashboard(customer_id: str) -> LineStatusResponse:
    try:
        return platform_service.get_dashboard(customer_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer '{exc.args[0]}' not found",
        ) from exc


@router.get(
    "/subscriptions/{subscription_id}/activation",
    response_model=ActivationStatusResponse,
    summary="Poll activation progress and next steps for a line",
)
async def get_activation_status(subscription_id: str) -> ActivationStatusResponse:
    try:
        return platform_service.get_activation_status(subscription_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription '{exc.args[0]}' not found",
        ) from exc
