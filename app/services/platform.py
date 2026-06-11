"""In-memory connectivity platform service for Nigeria-market workflows."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.schemas.connectivity import (
    ActivationStatusResponse,
    AppSessionRequest,
    AppSessionResponse,
    BundleInfo,
    ComplianceStatus,
    CustomerOnboardingRequest,
    CustomerProfileResponse,
    HubPolicyResponse,
    HubPolicySyncRequest,
    KYCStatus,
    LineStatusResponse,
    PhysicalSIMResponse,
    PhysicalSIMStatus,
    PlatformIntegrationResponse,
    PlatformMetricsResponse,
    ReadinessResponse,
    SIMAssignRequest,
    SimFormFactor,
    SIMInventoryRequest,
    SIMReplaceRequest,
    SubscriptionResponse,
    SubscriptionStatus,
)

_customer_store: dict[str, dict[str, Any]] = {}
_subscription_store: dict[str, dict[str, Any]] = {}
_physical_sim_store: dict[str, dict[str, Any]] = {}
_app_session_store: dict[str, dict[str, Any]] = {}
_hub_policy_store: dict[str, dict[str, Any]] = {}
_audit_log: list[dict[str, Any]] = []


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


def _record_event(action: str, entity_type: str, entity_id: str, **details: Any) -> None:
    _audit_log.append(
        {
            "event_id": _new_id("audit"),
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": details,
            "recorded_at": _now().isoformat(),
        }
    )


def _subscription_to_response(record: dict[str, Any]) -> SubscriptionResponse:
    return SubscriptionResponse.model_validate(record)


def _customer_to_response(record: dict[str, Any]) -> CustomerProfileResponse:
    return CustomerProfileResponse.model_validate(record)


def _sim_to_response(record: dict[str, Any]) -> PhysicalSIMResponse:
    return PhysicalSIMResponse.model_validate(record)


class ConnectivityPlatformService:
    """Coordinates customers, subscriptions, physical SIMs, app sessions, and hub policies."""

    def onboard_customer(self, request: CustomerOnboardingRequest) -> CustomerProfileResponse:
        customer_id = _new_id("cust")
        now = _now()
        profile = {
            "customer_id": customer_id,
            "full_name": request.full_name,
            "email": request.email,
            "phone_number": request.phone_number,
            "role": request.role,
            "kyc_status": KYCStatus.VERIFIED if request.nin_reference else KYCStatus.PENDING,
            "compliance_status": (
                ComplianceStatus.APPROVED
                if request.nin_reference
                else ComplianceStatus.PENDING_REVIEW
            ),
            "nin_reference": request.nin_reference,
            "allowed_bundles": request.allowed_bundles,
            "created_at": now,
            "metadata": request.metadata,
        }
        _customer_store[customer_id] = profile
        _record_event("CUSTOMER_ONBOARDED", "customer", customer_id, role=request.role)
        return _customer_to_response(profile)

    def get_customer(self, customer_id: str) -> CustomerProfileResponse:
        profile = _customer_store.get(customer_id)
        if profile is None:
            raise KeyError(customer_id)
        return _customer_to_response(profile)

    def get_customer_lines(self, customer_id: str) -> LineStatusResponse:
        customer = self.get_customer(customer_id)
        subscriptions = [
            _subscription_to_response(record)
            for record in _subscription_store.values()
            if record.get("customer_id") == customer_id
        ]
        bundles = [
            BundleInfo(bundle_id=bundle_id, name=bundle_id.replace("-", " ").title())
            for bundle_id in customer.allowed_bundles
        ]
        audit_events = [
            event
            for event in reversed(_audit_log)
            if event["entity_id"] == customer_id
            or event["details"].get("customer_id") == customer_id
            or event["details"].get("previous_customer_id") == customer_id
        ][:10]
        return LineStatusResponse(
            customer=customer,
            subscriptions=subscriptions,
            available_bundles=bundles,
            recent_audit_events=audit_events,
        )

    def create_app_session(self, request: AppSessionRequest) -> AppSessionResponse:
        self.get_customer(request.customer_id)
        issued_at = _now()
        session = {
            "session_id": _new_id("session"),
            "customer_id": request.customer_id,
            "channel": request.channel,
            "issued_at": issued_at,
            "expires_at": issued_at + timedelta(hours=8),
            "device_id": request.device_id,
        }
        _app_session_store[session["session_id"]] = session
        _record_event(
            "APP_SESSION_CREATED",
            "app_session",
            session["session_id"],
            customer_id=request.customer_id,
            channel=request.channel,
        )
        return AppSessionResponse.model_validate(session)

    def get_dashboard(self, customer_id: str) -> LineStatusResponse:
        return self.get_customer_lines(customer_id)

    def create_physical_sim(self, request: SIMInventoryRequest) -> PhysicalSIMResponse:
        if request.iccid in _physical_sim_store:
            raise ValueError(f"Physical SIM {request.iccid!r} already exists")

        now = _now()
        record = {
            "iccid": request.iccid,
            "serial_number": request.serial_number,
            "msisdn": request.msisdn,
            "status": PhysicalSIMStatus.INVENTORIED,
            "plan_id": request.plan_id,
            "preferred_network": request.preferred_network,
            "customer_id": None,
            "subscription_id": None,
            "device_id": None,
            "edge_id": request.edge_id,
            "activated_at": None,
            "deactivated_at": None,
            "created_at": now,
            "updated_at": now,
            "metadata": request.metadata,
        }
        _physical_sim_store[request.iccid] = record
        _record_event("SIM_INVENTORIED", "physical_sim", request.iccid, edge_id=request.edge_id)
        return _sim_to_response(record)

    def get_physical_sim(self, iccid: str) -> PhysicalSIMResponse:
        record = _physical_sim_store.get(iccid)
        if record is None:
            raise KeyError(iccid)
        return _sim_to_response(record)

    def assign_physical_sim(self, iccid: str, request: SIMAssignRequest) -> PhysicalSIMResponse:
        sim = _physical_sim_store.get(iccid)
        if sim is None:
            raise KeyError(iccid)
        self.get_customer(request.customer_id)

        if sim["status"] in {PhysicalSIMStatus.REPLACED, PhysicalSIMStatus.DEACTIVATED}:
            raise ValueError(f"Physical SIM {iccid!r} is not assignable in status {sim['status']}")

        now = _now()
        current_subscription_id = sim.get("subscription_id")
        subscription_id = (
            current_subscription_id if current_subscription_id is not None else _new_id("sub")
        )
        subscription_status = (
            SubscriptionStatus.ACTIVE if request.activate_immediately else SubscriptionStatus.READY
        )
        subscription = {
            "subscription_id": subscription_id,
            "customer_id": request.customer_id,
            "form_factor": SimFormFactor.PHYSICAL,
            "sim_identifier": iccid,
            "device_id": request.device_id,
            "status": subscription_status,
            "plan_id": sim["plan_id"],
            "preferred_network": sim["preferred_network"],
            "activation_code": None,
            "qr_code_url": None,
            "allowed_bundles": request.allowed_bundles,
            "activated_at": now if request.activate_immediately else None,
            "created_at": _subscription_store.get(subscription_id, {}).get("created_at", now),
            "updated_at": now,
        }
        _subscription_store[subscription_id] = subscription

        sim.update(
            {
                "status": (
                    PhysicalSIMStatus.ACTIVE
                    if request.activate_immediately
                    else PhysicalSIMStatus.ASSIGNED
                ),
                "customer_id": request.customer_id,
                "subscription_id": subscription_id,
                "device_id": request.device_id,
                "activated_at": now if request.activate_immediately else None,
                "updated_at": now,
            }
        )
        _record_event(
            "SIM_ASSIGNED",
            "physical_sim",
            iccid,
            customer_id=request.customer_id,
            subscription_id=subscription_id,
            fulfillment_reference=request.fulfillment_reference,
        )
        return _sim_to_response(sim)

    def activate_physical_sim(self, iccid: str) -> PhysicalSIMResponse:
        sim = _physical_sim_store.get(iccid)
        if sim is None:
            raise KeyError(iccid)
        if sim.get("subscription_id") is None:
            raise ValueError(
                f"Physical SIM {iccid!r} must be assigned to a customer before activation"
            )

        now = _now()
        sim.update(
            {
                "status": PhysicalSIMStatus.ACTIVE,
                "activated_at": now,
                "updated_at": now,
            }
        )
        subscription = _subscription_store[sim["subscription_id"]]
        subscription.update(
            {
                "status": SubscriptionStatus.ACTIVE,
                "activated_at": now,
                "updated_at": now,
            }
        )
        _record_event(
            "SIM_ACTIVATED",
            "physical_sim",
            iccid,
            customer_id=sim.get("customer_id"),
            subscription_id=sim["subscription_id"],
        )
        return _sim_to_response(sim)

    def suspend_physical_sim(self, iccid: str) -> PhysicalSIMResponse:
        sim = _physical_sim_store.get(iccid)
        if sim is None:
            raise KeyError(iccid)

        now = _now()
        sim.update({"status": PhysicalSIMStatus.SUSPENDED, "updated_at": now})
        if sim.get("subscription_id"):
            _subscription_store[sim["subscription_id"]].update(
                {"status": SubscriptionStatus.SUSPENDED, "updated_at": now}
            )
        _record_event("SIM_SUSPENDED", "physical_sim", iccid, customer_id=sim.get("customer_id"))
        return _sim_to_response(sim)

    def replace_physical_sim(self, iccid: str, request: SIMReplaceRequest) -> PhysicalSIMResponse:
        sim = _physical_sim_store.get(iccid)
        replacement = _physical_sim_store.get(request.replacement_iccid)
        if sim is None or replacement is None:
            raise KeyError(iccid if sim is None else request.replacement_iccid)
        if replacement["status"] != PhysicalSIMStatus.INVENTORIED:
            raise ValueError("Replacement physical SIM must be in INVENTORIED status")

        now = _now()
        replacement.update(
            {
                "status": PhysicalSIMStatus.ASSIGNED,
                "customer_id": sim.get("customer_id"),
                "subscription_id": sim.get("subscription_id"),
                "device_id": sim.get("device_id"),
                "updated_at": now,
            }
        )
        sim.update(
            {
                "status": PhysicalSIMStatus.REPLACED,
                "deactivated_at": now,
                "updated_at": now,
            }
        )
        if sim.get("subscription_id"):
            _subscription_store[sim["subscription_id"]].update(
                {
                    "sim_identifier": request.replacement_iccid,
                    "status": SubscriptionStatus.READY,
                    "updated_at": now,
                }
            )
        _record_event(
            "SIM_REPLACED",
            "physical_sim",
            iccid,
            replacement_iccid=request.replacement_iccid,
            customer_id=sim.get("customer_id"),
            reason=request.reason,
        )
        return _sim_to_response(replacement)

    def deactivate_physical_sim(self, iccid: str) -> PhysicalSIMResponse:
        sim = _physical_sim_store.get(iccid)
        if sim is None:
            raise KeyError(iccid)

        now = _now()
        sim.update(
            {
                "status": PhysicalSIMStatus.DEACTIVATED,
                "deactivated_at": now,
                "updated_at": now,
            }
        )
        if sim.get("subscription_id"):
            _subscription_store[sim["subscription_id"]].update(
                {"status": SubscriptionStatus.DEACTIVATED, "updated_at": now}
            )
        _record_event("SIM_DEACTIVATED", "physical_sim", iccid, customer_id=sim.get("customer_id"))
        return _sim_to_response(sim)

    def upsert_esim_subscription(
        self,
        *,
        customer_id: str | None,
        iccid: str,
        device_id: str,
        plan_id: str,
        preferred_network: Any,
        activation_code: str,
        qr_code_url: str,
        activated_at: datetime | None = None,
        status: SubscriptionStatus = SubscriptionStatus.PENDING,
    ) -> str:
        existing = next(
            (
                record
                for record in _subscription_store.values()
                if record["form_factor"] == SimFormFactor.ESIM and record["sim_identifier"] == iccid
            ),
            None,
        )
        subscription_id = existing["subscription_id"] if existing else _new_id("sub")
        created_at = existing["created_at"] if existing else _now()
        record = {
            "subscription_id": subscription_id,
            "customer_id": customer_id,
            "form_factor": SimFormFactor.ESIM,
            "sim_identifier": iccid,
            "device_id": device_id,
            "status": status,
            "plan_id": plan_id,
            "preferred_network": preferred_network,
            "activation_code": activation_code,
            "qr_code_url": qr_code_url,
            "allowed_bundles": (
                _customer_store.get(customer_id, {}).get("allowed_bundles", [])
                if customer_id
                else []
            ),
            "activated_at": activated_at,
            "created_at": created_at,
            "updated_at": _now(),
        }
        _subscription_store[subscription_id] = record
        _record_event(
            "ESIM_SUBSCRIPTION_UPSERTED",
            "subscription",
            subscription_id,
            customer_id=customer_id,
            iccid=iccid,
        )
        return subscription_id

    def update_subscription_status(
        self,
        subscription_id: str,
        *,
        status: SubscriptionStatus,
        activated_at: datetime | None = None,
        preferred_network: Any | None = None,
        plan_id: str | None = None,
    ) -> None:
        record = _subscription_store.get(subscription_id)
        if record is None:
            raise KeyError(subscription_id)

        record["status"] = status
        record["updated_at"] = _now()
        if activated_at is not None:
            record["activated_at"] = activated_at
        if preferred_network is not None:
            record["preferred_network"] = preferred_network
        if plan_id is not None:
            record["plan_id"] = plan_id

    def get_subscription(self, subscription_id: str) -> SubscriptionResponse:
        record = _subscription_store.get(subscription_id)
        if record is None:
            raise KeyError(subscription_id)
        return _subscription_to_response(record)

    def get_activation_status(self, subscription_id: str) -> ActivationStatusResponse:
        subscription = self.get_subscription(subscription_id)
        if subscription.form_factor == SimFormFactor.ESIM:
            ready = subscription.status in {
                SubscriptionStatus.PENDING,
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.SWITCHING,
            }
            next_step = (
                "Scan QR code in Aku-Telhone app to download the eSIM profile"
                if subscription.status == SubscriptionStatus.PENDING
                else "Line is already active"
            )
        else:
            ready = subscription.status in {SubscriptionStatus.READY, SubscriptionStatus.ACTIVE}
            next_step = (
                "Insert the physical SIM and complete activation in the Aku-Telhone app"
                if subscription.status == SubscriptionStatus.READY
                else "Line is already active"
            )
        return ActivationStatusResponse(
            subscription=subscription,
            ready_for_use=ready,
            next_step=next_step,
        )

    def sync_hub_policy(self, request: HubPolicySyncRequest) -> HubPolicyResponse:
        policy = {
            "edge_id": request.edge_id,
            "super_hub_id": request.super_hub_id,
            "education_qos_priority": request.education_qos_priority,
            "top_cached_assets": request.top_cached_assets,
            "preferred_call_route": request.preferred_call_route,
            "allowed_bundles": request.allowed_bundles,
            "synced_at": _now(),
        }
        _hub_policy_store[request.edge_id] = policy
        _record_event(
            "HUB_POLICY_SYNCED",
            "hub_policy",
            request.edge_id,
            super_hub_id=request.super_hub_id,
        )
        return HubPolicyResponse.model_validate(policy)

    def get_hub_policy(self, edge_id: str) -> HubPolicyResponse:
        policy = _hub_policy_store.get(edge_id)
        if policy is None:
            raise KeyError(edge_id)
        return HubPolicyResponse.model_validate(policy)

    def get_integration_contracts(self) -> PlatformIntegrationResponse:
        return PlatformIntegrationResponse(
            service="Aku-Telhone",
            responsibilities={
                "aku_telhone": [
                    "Provision and lifecycle-manage eSIM and physical SIM subscriptions",
                    "Expose consumer and operator APIs for onboarding, line status, and activation",
                    "Publish hub policy, bundle eligibility, and connectivity metadata to edge services",
                ],
                "edge_hub": [
                    "Handle local SIP registration, low-latency call relay, and edge cache delivery",
                ],
                "super_hub": [
                    "Coordinate regional call control, predictive prefetch, and mediation collection",
                ],
                "ig_hub": [
                    "Own global policy, SIM provisioning policy, and cross-region federation",
                ],
            },
            exposed_interfaces={
                "consumer_apis": [
                    "/api/v1/app/sessions",
                    "/api/v1/app/customers/{customer_id}/dashboard",
                    "/api/v1/app/subscriptions/{subscription_id}/activation",
                ],
                "operator_apis": [
                    "/api/v1/customers/onboard",
                    "/api/v1/sims/inventory",
                    "/api/v1/platform/hub-policy-sync",
                ],
                "observability": ["/health", "/readyz", "/metrics"],
            },
        )

    def get_metrics(self) -> PlatformMetricsResponse:
        return PlatformMetricsResponse(
            customers_total=len(_customer_store),
            subscriptions_total=len(_subscription_store),
            esim_subscriptions_total=sum(
                1
                for record in _subscription_store.values()
                if record["form_factor"] == SimFormFactor.ESIM
            ),
            physical_sims_total=len(_physical_sim_store),
            physical_sims_active_total=sum(
                1
                for record in _physical_sim_store.values()
                if record["status"] == PhysicalSIMStatus.ACTIVE
            ),
            app_sessions_total=len(_app_session_store),
            audit_events_total=len(_audit_log),
            hub_policies_total=len(_hub_policy_store),
        )

    def get_metrics_text(self) -> str:
        metrics = self.get_metrics()
        return "\n".join(
            [
                "# HELP aku_customers_total Total onboarded customers",
                "# TYPE aku_customers_total gauge",
                f"aku_customers_total {metrics.customers_total}",
                "# HELP aku_subscriptions_total Total subscriptions",
                "# TYPE aku_subscriptions_total gauge",
                f"aku_subscriptions_total {metrics.subscriptions_total}",
                "# HELP aku_esim_subscriptions_total Total eSIM subscriptions",
                "# TYPE aku_esim_subscriptions_total gauge",
                f"aku_esim_subscriptions_total {metrics.esim_subscriptions_total}",
                "# HELP aku_physical_sims_total Total physical SIM records",
                "# TYPE aku_physical_sims_total gauge",
                f"aku_physical_sims_total {metrics.physical_sims_total}",
                "# HELP aku_physical_sims_active_total Active physical SIM records",
                "# TYPE aku_physical_sims_active_total gauge",
                f"aku_physical_sims_active_total {metrics.physical_sims_active_total}",
                "# HELP aku_app_sessions_total Total active app sessions issued",
                "# TYPE aku_app_sessions_total gauge",
                f"aku_app_sessions_total {metrics.app_sessions_total}",
                "# HELP aku_audit_events_total Total audit trail events",
                "# TYPE aku_audit_events_total gauge",
                f"aku_audit_events_total {metrics.audit_events_total}",
                "# HELP aku_hub_policies_total Total synced hub policy records",
                "# TYPE aku_hub_policies_total gauge",
                f"aku_hub_policies_total {metrics.hub_policies_total}",
                "",
            ]
        )

    def get_readiness(self) -> ReadinessResponse:
        return ReadinessResponse(
            status="ready",
            checks={
                "profile_store": "ok",
                "subscription_store": "ok",
                "customer_store": "ok",
                "hub_policy_store": "ok",
            },
        )


platform_service = ConnectivityPlatformService()
