"""Customer onboarding and subscription visibility APIs."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas.connectivity import (
    CustomerOnboardingRequest,
    CustomerProfileResponse,
    LineStatusResponse,
)
from app.services.platform import platform_service

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


@router.post(
    "/onboard",
    response_model=CustomerProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Onboard a Nigerian-market customer",
)
async def onboard_customer(body: CustomerOnboardingRequest) -> CustomerProfileResponse:
    return platform_service.onboard_customer(body)


@router.get(
    "/{customer_id}",
    response_model=CustomerProfileResponse,
    summary="Get customer compliance and profile data",
)
async def get_customer(customer_id: str) -> CustomerProfileResponse:
    try:
        return platform_service.get_customer(customer_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer '{customer_id}' not found",
        ) from exc


@router.get(
    "/{customer_id}/lines",
    response_model=LineStatusResponse,
    summary="List all customer lines and bundles",
)
async def get_customer_lines(customer_id: str) -> LineStatusResponse:
    try:
        return platform_service.get_customer_lines(customer_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer '{customer_id}' not found",
        ) from exc
