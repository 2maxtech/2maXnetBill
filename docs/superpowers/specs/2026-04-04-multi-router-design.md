# Multi-Router MikroTik Support — Design Spec

## Overview

Add support for managing multiple MikroTik routers from a single NetLedger instance. ISP operators typically have 3-10 routers across different areas/towers. Each customer is assigned to a specific router (directly or via an area). NetLedger manages PPPoE secrets and profiles on each router independently. The operator pre-configures the PPPoE server on each MikroTik via WinBox — NetLedger only manages the subscriber lifecycle (secrets, profiles, enable/disable).

## Architecture

```
NetLedger (192.168.40.40)
├── Router: "MT-Barangay1" (192.168.40.30)
│   ├── Customer: Juan → PPPoE secret
│   ├── Customer: Maria → PPPoE secret
│   └── Profile: 10M-5M
├── Router: "MT-Barangay2" (192.168.40.31)
│   ├── Customer: Pedro → PPPoE secret
│   └── Profile: 20M-10M
└── Dashboard: aggregated stats from all routers
```

## New Database Tables

### `routers`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| name | String(100) | e.g. "MT-Barangay1" |
| url | String(255) | e.g. "http://192.168.40.30" |
| username | String(100) | MikroTik admin user |
| password | String(255) | MikroTik admin password |
| location | String(255), nullable | e.g. "Barangay San Jose Tower 1" |
| is_active | Boolean, default True | |
| created_at | DateTime | auto |

### `areas`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| name | String(100) | e.g. "Barangay San Jose" |
| description | Text, nullable | |
| router_id | UUID (FK → routers), nullable | Default router for this area |
| created_at | DateTime | auto |

### Customer Model Changes

Add two new columns:
- `router_id: UUID (FK → routers), nullable` — direct router assignment (overrides area)
- `area_id: UUID (FK → areas), nullable` — area assignment

**Router resolution order:**
1. `customer.router_id` (direct assignment)
2. `customer.area.router_id` (area's default router)
3. System default router (first active router, or from `MIKROTIK_*` env vars)

If no router can be resolved, MikroTik operations are skipped with a warning log.

## MikroTik Client Changes

### Remove Singleton

Replace the module-level `mikrotik = MikroTikClient()` singleton with a factory + cache:

```python
_client_cache: dict[str, MikroTikClient] = {}

def get_mikrotik_client(router_id: str | None = None, url: str = None, user: str = None, password: str = None) -> MikroTikClient:
    """Get or create a MikroTikClient for a specific router."""

async def get_client_for_customer(db: AsyncSession, customer: Customer) -> tuple[MikroTikClient | None, str | None]:
    """Resolve the customer's router and return (client, router_id). Returns (None, None) if no router."""
```

The cache is keyed by router UUID. When router credentials are updated via API, the cached client is invalidated.

### Helper: get_customer_router

```python
async def get_customer_router(db: AsyncSession, customer: Customer) -> Router | None:
    """Resolve router for a customer: direct → area → default."""
```

## API Routes

### Router CRUD (`backend/app/api/admin/routers.py`)

```
POST   /api/v1/routers/              Create router
GET    /api/v1/routers/              List all routers
GET    /api/v1/routers/{id}          Get router details
PUT    /api/v1/routers/{id}          Update router (invalidates client cache)
DELETE /api/v1/routers/{id}          Soft-delete (set is_active=False)
GET    /api/v1/routers/{id}/status   Health check (identity, resources, session count)
POST   /api/v1/routers/{id}/import   Import subscribers from this router
```

### Area CRUD (`backend/app/api/admin/areas.py`)

```
POST   /api/v1/areas/                Create area
GET    /api/v1/areas/                List all areas
PUT    /api/v1/areas/{id}            Update area
DELETE /api/v1/areas/{id}            Delete area
```

### Customer Changes

- `CustomerCreate` and `CustomerUpdate` schemas add `router_id` and `area_id` (both optional)
- `CustomerResponse` includes `router_id`, `area_id`, and nested `router` and `area` objects
- Customer create auto-provisions on the resolved router
- Customer update re-provisions if router changes

### Dashboard Changes

`GET /api/v1/network/dashboard` updated to:
- Query all active routers
- Fetch MikroTik stats from each router in parallel (asyncio.gather)
- Return per-router health + aggregated totals
- Include `routers` array in response with per-router stats

### Network Routes Changes

- `GET /network/active-sessions` accepts optional `?router_id=` filter
- `GET /network/subscribers` accepts optional `?router_id=` filter
- `POST /network/import` requires `router_id` in body (no more global import)

## Billing Integration Changes

All MikroTik calls in `billing.py` and `customers.py` must resolve the customer's router before making API calls:

```python
# Before (singleton):
from app.services.mikrotik import mikrotik
await mikrotik.enable_secret(customer.mikrotik_secret_id)

# After (per-router):
from app.services.mikrotik import get_client_for_customer
client, router_id = await get_client_for_customer(db, customer)
if client:
    await client.enable_secret(customer.mikrotik_secret_id)
```

This pattern applies to:
- `record_payment` → enable_secret + update profile
- `process_graduated_disconnect` → throttle profile / disable_secret
- `create_customer` → create_secret + ensure_profile
- `disconnect/reconnect/throttle_customer` → disable/enable/update_secret

## Frontend Changes

### New Pages

**Routers page** (`/routers`):
- Table: name, URL, location, status (online/offline), active sessions, actions
- Add/Edit router modal (name, URL, username, password, location)
- Status indicator (green/red badge) with auto-refresh
- "Import Subscribers" button per router
- "Test Connection" button

**Areas page** (`/areas`):
- Table: name, description, assigned router, customer count
- Add/Edit area modal

### Modified Pages

**Customer create/edit form:**
- Add Area dropdown (optional)
- Add Router dropdown (optional, overrides area)

**Dashboard:**
- Per-router health cards in a scrollable row
- Router filter dropdown
- Aggregated totals at top

**Active Users:**
- Router filter dropdown
- Show which router each session is on

### Sidebar

Add under System or as top-level:
- Routers (new)
- Areas (new)

## Migration Path

### Alembic Migration

1. Create `routers` table
2. Create `areas` table
3. Add `router_id` and `area_id` to `customers`
4. **Auto-migrate existing data:** Create a "Default" router from `MIKROTIK_*` env vars, assign all existing customers with `mikrotik_secret_id` to this router

### Config Backward Compatibility

`MIKROTIK_*` env vars remain as fallback defaults. When no routers exist in the DB, the system creates one from env vars on first API call.

## What Stays the Same

- Billing engine logic (invoices, payments, graduated disconnect flow)
- Customer portal
- Invoice PDF generation
- Email notifications
- Celery task schedule
- Auth system
- Plan management (plans are global, not per-router)
- Profiles are created per-router as needed (same plan can have profiles on multiple routers)

## Schema Summary

```
Router 1──M Customer
Area   1──M Customer
Area   M──1 Router (default router for area)
Customer resolves router: direct → area → system default
```
