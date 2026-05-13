"""Platform integration, policy sync, and observability endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status

from app.schemas.connectivity import (
    HubPolicyResponse,
    HubPolicySyncRequest,
    PlatformIntegrationResponse,
    PlatformMetricsResponse,
    ReadinessResponse,
    SubscriptionResponse,
)
from app.services.platform import platform_service

router = APIRouter(tags=["platform"])


@router.get(
    "/api/v1/subscriptions/{subscription_id}",
    response_model=SubscriptionResponse,
    summary="Get a unified subscription record",
)
async def get_subscription(subscription_id: str) -> SubscriptionResponse:
    try:
        return platform_service.get_subscription(subscription_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription '{exc.args[0]}' not found",
        ) from exc


@router.get(
    "/api/v1/platform/integration-contracts",
    response_model=PlatformIntegrationResponse,
    summary="Describe Aku-Telhone service boundaries and integrations",
)
async def get_integration_contracts() -> PlatformIntegrationResponse:
    return platform_service.get_integration_contracts()


@router.post(
    "/api/v1/platform/hub-policy-sync",
    response_model=HubPolicyResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Sync hub policy and predictive cache hints from IG-Hub/Super Hub",
)
async def sync_hub_policy(body: HubPolicySyncRequest) -> HubPolicyResponse:
    return platform_service.sync_hub_policy(body)


@router.get(
    "/api/v1/platform/hub-policy-sync/{edge_id}",
    response_model=HubPolicyResponse,
    summary="Get the latest synced policy for an Edge Hub",
)
async def get_hub_policy(edge_id: str) -> HubPolicyResponse:
    try:
        return platform_service.get_hub_policy(edge_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hub policy for edge '{exc.args[0]}' not found",
        ) from exc


@router.get(
    "/readyz",
    response_model=ReadinessResponse,
    summary="Readiness probe for orchestration",
)
async def readyz() -> ReadinessResponse:
    return platform_service.get_readiness()


@router.get(
    "/api/v1/platform/metrics",
    response_model=PlatformMetricsResponse,
    summary="Structured platform metrics snapshot",
)
async def get_platform_metrics() -> PlatformMetricsResponse:
    return platform_service.get_metrics()


@router.get(
    "/metrics",
    summary="Prometheus metrics",
    response_class=Response,
)
async def metrics() -> Response:
    return Response(
        content=platform_service.get_metrics_text(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
