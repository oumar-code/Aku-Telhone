"""Shared connectivity schemas for eSIM, physical SIM, app, and hub workflows."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.esim import NetworkTechnology


class SimFormFactor(StrEnum):
    ESIM = "ESIM"
    PHYSICAL = "PHYSICAL"


class SubscriptionStatus(StrEnum):
    PENDING = "PENDING"
    READY = "READY"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    SWITCHING = "SWITCHING"
    DEACTIVATED = "DEACTIVATED"


class PhysicalSIMStatus(StrEnum):
    INVENTORIED = "INVENTORIED"
    ASSIGNED = "ASSIGNED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REPLACED = "REPLACED"
    DEACTIVATED = "DEACTIVATED"


class KYCStatus(StrEnum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class ComplianceStatus(StrEnum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    RESTRICTED = "RESTRICTED"


class UserRole(StrEnum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    STAFF = "STAFF"
    ADMIN = "ADMIN"


class BundleInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    bundle_id: str
    name: str
    category: str = "education"
    active: bool = True


class CustomerOnboardingRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    full_name: str = Field(..., min_length=3, description="Subscriber full legal name")
    email: str | None = Field(None, description="Primary email used by the Aku-Telhony app")
    phone_number: str | None = Field(None, description="Primary reachable phone number")
    nin_reference: str | None = Field(
        None,
        description="Opaque NIN/KYC reference from the compliance provider; raw NIN is not stored",
    )
    role: UserRole = Field(UserRole.STUDENT, description="Subscriber role for policy enforcement")
    allowed_bundles: list[str] = Field(
        default_factory=list,
        description="Bundle identifiers the subscriber is eligible to activate",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Free-form onboarding context such as state, school, or partner channel",
    )


class CustomerProfileResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    customer_id: str
    full_name: str
    email: str | None = None
    phone_number: str | None = None
    role: UserRole
    kyc_status: KYCStatus
    compliance_status: ComplianceStatus
    nin_reference: str | None = None
    allowed_bundles: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    subscription_id: str
    customer_id: str | None = None
    form_factor: SimFormFactor
    sim_identifier: str
    device_id: str | None = None
    status: SubscriptionStatus
    plan_id: str
    preferred_network: NetworkTechnology
    activation_code: str | None = None
    qr_code_url: str | None = None
    allowed_bundles: list[str] = Field(default_factory=list)
    activated_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SIMInventoryRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    iccid: str = Field(..., min_length=10, description="Physical SIM ICCID")
    serial_number: str = Field(..., description="Printed SIM serial number")
    msisdn: str | None = Field(None, description="Assigned Nigerian phone number when available")
    plan_id: str = Field(..., description="Default plan linked to the SIM inventory item")
    preferred_network: NetworkTechnology = NetworkTechnology.LTE
    edge_id: str | None = Field(None, description="Preferred Edge Hub for distribution")
    metadata: dict[str, Any] = Field(default_factory=dict)


class SIMAssignRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    customer_id: str
    device_id: str | None = None
    activate_immediately: bool = False
    allowed_bundles: list[str] = Field(default_factory=list)
    fulfillment_reference: str | None = None


class SIMReplaceRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    replacement_iccid: str = Field(..., description="New physical SIM ICCID")
    reason: str = Field(..., min_length=3, max_length=512)


class PhysicalSIMResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    iccid: str
    serial_number: str
    msisdn: str | None = None
    status: PhysicalSIMStatus
    plan_id: str
    preferred_network: NetworkTechnology
    customer_id: str | None = None
    subscription_id: str | None = None
    device_id: str | None = None
    edge_id: str | None = None
    activated_at: datetime | None = None
    deactivated_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AppSessionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    customer_id: str
    channel: str = Field("mobile", description="Client channel: mobile | web")
    device_id: str | None = None


class AppSessionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: str
    customer_id: str
    channel: str
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime


class LineStatusResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    customer: CustomerProfileResponse
    subscriptions: list[SubscriptionResponse] = Field(default_factory=list)
    available_bundles: list[BundleInfo] = Field(default_factory=list)
    recent_audit_events: list[dict[str, Any]] = Field(default_factory=list)


class ActivationStatusResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    subscription: SubscriptionResponse
    ready_for_use: bool
    next_step: str


class HubPolicySyncRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    edge_id: str
    super_hub_id: str
    education_qos_priority: bool = True
    top_cached_assets: list[str] = Field(default_factory=list)
    preferred_call_route: str = Field(
        "LOCAL_EDGE", description="LOCAL_EDGE | SUPER_HUB | MNO_GATEWAY"
    )
    allowed_bundles: list[str] = Field(default_factory=list)


class HubPolicyResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    edge_id: str
    super_hub_id: str
    education_qos_priority: bool
    top_cached_assets: list[str]
    preferred_call_route: str
    allowed_bundles: list[str]
    synced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PlatformIntegrationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    service: str
    responsibilities: dict[str, list[str]]
    exposed_interfaces: dict[str, list[str]]


class PlatformMetricsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    customers_total: int
    subscriptions_total: int
    esim_subscriptions_total: int
    physical_sims_total: int
    physical_sims_active_total: int
    app_sessions_total: int
    audit_events_total: int
    hub_policies_total: int


class ReadinessResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: str
    checks: dict[str, str]
