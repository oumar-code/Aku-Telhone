"""Physical SIM inventory and lifecycle APIs."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas.connectivity import (
    PhysicalSIMResponse,
    SIMAssignRequest,
    SIMInventoryRequest,
    SIMReplaceRequest,
)
from app.services.platform import platform_service

router = APIRouter(prefix="/api/v1/sims", tags=["physical-sims"])


@router.post(
    "/inventory",
    response_model=PhysicalSIMResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a physical SIM inventory record",
)
async def create_inventory_record(body: SIMInventoryRequest) -> PhysicalSIMResponse:
    try:
        return platform_service.create_physical_sim(body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "/{iccid}",
    response_model=PhysicalSIMResponse,
    summary="Get a physical SIM record",
)
async def get_physical_sim(iccid: str) -> PhysicalSIMResponse:
    try:
        return platform_service.get_physical_sim(iccid)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Physical SIM '{iccid}' not found",
        ) from exc


@router.post(
    "/{iccid}/assign",
    response_model=PhysicalSIMResponse,
    summary="Assign a physical SIM to a customer/device",
)
async def assign_physical_sim(iccid: str, body: SIMAssignRequest) -> PhysicalSIMResponse:
    try:
        return platform_service.assign_physical_sim(iccid, body)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Physical SIM or customer not found: {exc.args[0]}",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/{iccid}/activate",
    response_model=PhysicalSIMResponse,
    summary="Activate an assigned physical SIM",
)
async def activate_physical_sim(iccid: str) -> PhysicalSIMResponse:
    try:
        return platform_service.activate_physical_sim(iccid)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Physical SIM '{iccid}' not found",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/{iccid}/suspend",
    response_model=PhysicalSIMResponse,
    summary="Suspend a physical SIM and linked subscription",
)
async def suspend_physical_sim(iccid: str) -> PhysicalSIMResponse:
    try:
        return platform_service.suspend_physical_sim(iccid)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Physical SIM '{iccid}' not found",
        ) from exc


@router.post(
    "/{iccid}/replace",
    response_model=PhysicalSIMResponse,
    summary="Swap a physical SIM to a replacement SIM",
)
async def replace_physical_sim(iccid: str, body: SIMReplaceRequest) -> PhysicalSIMResponse:
    try:
        return platform_service.replace_physical_sim(iccid, body)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Replacement flow record not found: {exc.args[0]}",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{iccid}",
    response_model=PhysicalSIMResponse,
    summary="Deactivate a physical SIM",
)
async def deactivate_physical_sim(iccid: str) -> PhysicalSIMResponse:
    try:
        return platform_service.deactivate_physical_sim(iccid)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Physical SIM '{iccid}' not found",
        ) from exc
