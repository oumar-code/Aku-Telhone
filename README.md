# Aku-Telhone — Nigeria Connectivity Platform

Aku-Telhone is the connectivity orchestration service for Aku's Nigerian rollout. It now supports:

- **eSIM lifecycle management** for newer devices
- **physical SIM inventory and lifecycle management** for the wider Nigerian handset market
- **customer onboarding and compliance hooks** for KYC / NIN-linked operations
- **Aku-Telhony app APIs** for dashboard, activation progress, and line visibility
- **Edge Hub / Super Hub / IG-Hub integration contracts** for VoIP, policy, and caching coordination
- **observability endpoints** for health, readiness, and Prometheus metrics

> The repository still uses in-memory stores for prototype flows. Replace them with durable database / Redis-backed implementations before production rollout.

---

## Platform scope

### Aku-Telhone owns
- eSIM provisioning, OTA switching, and deactivation
- physical SIM inventory, assignment, activation, suspension, replacement, and deactivation
- unified subscription records across eSIM and physical SIM lines
- customer onboarding metadata, bundle eligibility, and compliance state hooks
- app-facing APIs for activation and line management
- hub policy synchronization and connectivity metadata exposure

### Adjacent services own
- **Edge Hub**: local SIP registration, RTP relay, edge cache delivery, local call offload
- **Super Hub**: regional softswitch, predictive prefetch orchestration, mediation/CDR collection
- **IG-Hub**: global policy, SIM policy authority, cross-region routing and clearing, attestation federation

Aku-Telhone exposes the provisioning and policy interfaces those services consume, but it does **not** embed Kamailio, FreeSWITCH, or cache engines directly.

---

## API surface

### eSIM APIs
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/esim/provision` | Provision a new eSIM and create a unified subscription |
| `GET` | `/api/v1/esim/{iccid}` | Fetch eSIM profile state |
| `PATCH` | `/api/v1/esim/{iccid}/switch-network` | Trigger OTA network switch |
| `POST` | `/api/v1/esim/{iccid}/ota-push` | Trigger OTA push |
| `DELETE` | `/api/v1/esim/{iccid}` | Deactivate eSIM profile |

### Physical SIM APIs
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/sims/inventory` | Register SIM stock |
| `GET` | `/api/v1/sims/{iccid}` | Fetch physical SIM record |
| `POST` | `/api/v1/sims/{iccid}/assign` | Bind SIM to customer / device |
| `POST` | `/api/v1/sims/{iccid}/activate` | Activate assigned physical SIM |
| `POST` | `/api/v1/sims/{iccid}/suspend` | Suspend SIM and linked subscription |
| `POST` | `/api/v1/sims/{iccid}/replace` | Replace SIM with a new physical SIM |
| `DELETE` | `/api/v1/sims/{iccid}` | Deactivate physical SIM |

### Customer and app APIs
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/customers/onboard` | Create customer profile with compliance hooks |
| `GET` | `/api/v1/customers/{customer_id}` | Fetch customer profile |
| `GET` | `/api/v1/customers/{customer_id}/lines` | List subscriptions, bundles, and audit events |
| `POST` | `/api/v1/app/sessions` | Create app session for mobile/web clients |
| `GET` | `/api/v1/app/customers/{customer_id}/dashboard` | App dashboard payload |
| `GET` | `/api/v1/app/subscriptions/{subscription_id}/activation` | Poll activation progress and next steps |
| `GET` | `/api/v1/subscriptions/{subscription_id}` | Unified subscription record |

### Integration and ops APIs
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/devices/{device_id}/attest` | Proxy device attestation to Aku-IGHub |
| `GET` | `/api/v1/platform/integration-contracts` | Service-boundary contract for Edge/Super/IG hubs |
| `POST` | `/api/v1/platform/hub-policy-sync` | Sync edge policy and predictive cache hints |
| `GET` | `/api/v1/platform/hub-policy-sync/{edge_id}` | Get latest Edge Hub policy |
| `GET` | `/api/v1/platform/metrics` | Structured JSON metrics snapshot |
| `GET` | `/health` | Liveness probe |
| `GET` | `/readyz` | Readiness probe |
| `GET` | `/metrics` | Prometheus metrics |

---

## Quick start

```bash
# 1. Copy environment config
cp /home/runner/work/Aku-Telhone/Aku-Telhone/.env.example /home/runner/work/Aku-Telhone/Aku-Telhone/.env

# 2. Install dependencies
cd /home/runner/work/Aku-Telhone/Aku-Telhone
pip install -r requirements.txt -r requirements-extra.txt -r requirements-dev.txt

# 3. Run the API
uvicorn app.main:app --reload --port 8001
```

Interactive docs:
- Swagger UI: `http://localhost:8001/api/docs`
- OpenAPI JSON: `http://localhost:8001/api/openapi.json`

---

## Validation

```bash
cd /home/runner/work/Aku-Telhone/Aku-Telhone
ruff check .
black --check .
PYTHONPATH=. pytest --cov=app --cov-report=term-missing -v
```

---

## Nigeria-market domain model

### Shared subscription model
Every line is represented as a unified subscription with:
- `subscription_id`
- `customer_id`
- `form_factor` = `ESIM` or `PHYSICAL`
- `sim_identifier`
- `plan_id`
- `preferred_network`
- activation status and timestamps

This allows the Aku-Telhony app to treat eSIM and physical SIM lines consistently.

### Compliance hooks
Customer onboarding stores:
- customer identity metadata
- role-based eligibility (`STUDENT`, `TEACHER`, `STAFF`, `ADMIN`)
- allowed bundles
- `nin_reference` instead of raw NIN storage
- `kyc_status` and `compliance_status`

### Physical SIM lifecycle
```text
INVENTORIED -> ASSIGNED -> ACTIVE -> SUSPENDED
      |            |
      |            +-> REPLACED
      +-----------------> DEACTIVATED
```

### eSIM lifecycle
```text
PENDING -> ACTIVE -> SWITCHING -> ACTIVE
   |
   +-> DEACTIVATED
```

---

## Hub and caching integration model

### Edge Hub
- local SIP registration and low-latency call routing
- RTP/media relay
- edge cache for community-priority content
- local QoS enforcement for education traffic

### Super Hub
- regional call control and federation
- predictive content prefetch orchestration
- mediation / billing event aggregation
- routing optimization support

### IG-Hub
- global policy authority
- SIM policy and interconnect governance
- cross-state routing and provisioning decisions

Aku-Telhone contributes:
- subscriber policy metadata
- bundle eligibility
- edge policy sync payloads
- activation and line state required by upstream call-routing services

---

## Project layout

```text
Aku-Telhone/
├── app/
│   ├── main.py
│   ├── core/config.py
│   ├── routers/
│   │   ├── esim.py
│   │   ├── sims.py
│   │   ├── customers.py
│   │   ├── app_api.py
│   │   ├── platform.py
│   │   └── devices.py
│   ├── schemas/
│   │   ├── esim.py
│   │   └── connectivity.py
│   └── services/
│       ├── esim.py
│       ├── ota.py
│       └── platform.py
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   └── test_connectivity_platform.py
├── openapi.yaml
└── .env.example
```

---

## Production hardening still required

Before a production Nigerian rollout, replace prototype pieces with:
- persistent customer / SIM / subscription storage
- durable background job orchestration for OTA operations
- authenticated app sessions and operator access control
- real SM-DP+, OTA, and compliance-provider integrations
- event publication to Edge Hub / Super Hub / IG-Hub infrastructure
- production Prometheus / tracing / audit pipelines
