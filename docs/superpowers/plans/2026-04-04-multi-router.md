# Multi-Router MikroTik Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Support multiple MikroTik routers per NetLedger instance with area-based customer assignment and per-router dashboard stats.

**Architecture:** New Router and Area models in PostgreSQL. MikroTikClient instances cached per router ID. Customer resolves router via direct assignment → area default → system default. Dashboard aggregates stats from all routers in parallel.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 async, Alembic, httpx, React 18 + TypeScript + Ant Design

---

## File Structure

| Action | File | Purpose |
|--------|------|---------|
| Create | `backend/app/models/router.py` | Router + Area SQLAlchemy models |
| Create | `backend/app/schemas/router.py` | Router + Area Pydantic schemas |
| Create | `backend/app/api/admin/routers.py` | Router CRUD + status + import API |
| Create | `backend/app/api/admin/areas.py` | Area CRUD API |
| Create | `backend/alembic/versions/004_multi_router.py` | DB migration |
| Create | `frontend/src/api/routers.ts` | Router + Area API client |
| Create | `frontend/src/pages/Routers.tsx` | Routers management page |
| Create | `frontend/src/pages/Areas.tsx` | Areas management page |
| Modify | `backend/app/models/__init__.py` | Register Router, Area models |
| Modify | `backend/app/models/customer.py` | Add router_id, area_id FKs |
| Modify | `backend/app/schemas/customer.py` | Add router_id, area_id fields |
| Modify | `backend/app/services/mikrotik.py` | Replace singleton with factory + cache |
| Modify | `backend/app/services/billing.py` | Use get_client_for_customer |
| Modify | `backend/app/api/admin/customers.py` | Use per-router client, accept router_id/area_id |
| Modify | `backend/app/api/admin/network.py` | Per-router dashboard, router_id filters |
| Modify | `backend/app/api/admin/plans.py` | Sync profiles to all active routers |
| Modify | `backend/app/main.py` | Register routers + areas API routers |
| Modify | `frontend/src/components/Layout/SideMenu.tsx` | Add Routers, Areas menu items |
| Modify | `frontend/src/pages/Dashboard.tsx` | Per-router health cards |
| Modify | `frontend/src/pages/ActiveUsers.tsx` | Router filter dropdown |

---

### Task 1: Router and Area Models + Migration

**Files:**
- Create: `backend/app/models/router.py`
- Create: `backend/alembic/versions/004_multi_router.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/models/customer.py`

- [ ] **Step 1: Create Router and Area models**

```python
# backend/app/models/router.py
import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Router(BaseModel):
    __tablename__ = "routers"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False, default="admin")
    password: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    areas = relationship("Area", back_populates="router", lazy="selectin")


class Area(BaseModel):
    __tablename__ = "areas"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    router_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routers.id"), nullable=True
    )

    router = relationship("Router", back_populates="areas", lazy="selectin")
```

- [ ] **Step 2: Add router_id and area_id to Customer model**

In `backend/app/models/customer.py`, add after the `mac_address` field:

```python
    router_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routers.id"), nullable=True
    )
    area_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("areas.id"), nullable=True
    )

    router = relationship("Router", lazy="selectin")
    area = relationship("Area", lazy="selectin")
```

- [ ] **Step 3: Register models in __init__.py**

Add to `backend/app/models/__init__.py`:

```python
from app.models.router import Area, Router  # noqa: F401
```

- [ ] **Step 4: Create Alembic migration**

```python
# backend/alembic/versions/004_multi_router.py
"""add routers and areas tables, link customers

Revision ID: 004_multi_router
Revises: 003_mikrotik
Create Date: 2026-04-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '004_multi_router'
down_revision = '003_mikrotik'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'routers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('url', sa.String(255), nullable=False),
        sa.Column('username', sa.String(100), nullable=False, server_default='admin'),
        sa.Column('password', sa.String(255), nullable=False, server_default=''),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'areas',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('router_id', UUID(as_uuid=True), sa.ForeignKey('routers.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.add_column('customers', sa.Column('router_id', UUID(as_uuid=True), sa.ForeignKey('routers.id'), nullable=True))
    op.add_column('customers', sa.Column('area_id', UUID(as_uuid=True), sa.ForeignKey('areas.id'), nullable=True))


def downgrade() -> None:
    op.drop_column('customers', 'area_id')
    op.drop_column('customers', 'router_id')
    op.drop_table('areas')
    op.drop_table('routers')
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/router.py backend/app/models/__init__.py backend/app/models/customer.py backend/alembic/versions/004_multi_router.py
git commit -m "feat: add Router and Area models with customer assignment"
```

---

### Task 2: Router and Area Schemas

**Files:**
- Create: `backend/app/schemas/router.py`
- Modify: `backend/app/schemas/customer.py`

- [ ] **Step 1: Create router/area schemas**

```python
# backend/app/schemas/router.py
import uuid
from datetime import datetime

from pydantic import BaseModel


class RouterCreate(BaseModel):
    name: str
    url: str
    username: str = "admin"
    password: str = ""
    location: str | None = None


class RouterUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    username: str | None = None
    password: str | None = None
    location: str | None = None
    is_active: bool | None = None


class RouterResponse(BaseModel):
    id: uuid.UUID
    name: str
    url: str
    username: str
    location: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RouterStatusResponse(BaseModel):
    id: uuid.UUID
    name: str
    connected: bool
    identity: str | None = None
    uptime: str | None = None
    cpu_load: str | None = None
    free_memory: int = 0
    total_memory: int = 0
    active_sessions: int = 0
    version: str | None = None
    error: str | None = None


class AreaCreate(BaseModel):
    name: str
    description: str | None = None
    router_id: uuid.UUID | None = None


class AreaUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    router_id: uuid.UUID | None = None


class AreaResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    router_id: uuid.UUID | None
    router: RouterResponse | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Update customer schemas**

Add `router_id` and `area_id` to all three customer schemas in `backend/app/schemas/customer.py`:

In `CustomerCreate`, add:
```python
    router_id: uuid.UUID | None = None
    area_id: uuid.UUID | None = None
```

In `CustomerUpdate`, add:
```python
    router_id: uuid.UUID | None = None
    area_id: uuid.UUID | None = None
```

In `CustomerResponse`, add:
```python
    router_id: uuid.UUID | None = None
    area_id: uuid.UUID | None = None
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/router.py backend/app/schemas/customer.py
git commit -m "feat: add Router and Area schemas, update Customer schemas"
```

---

### Task 3: MikroTik Client — Replace Singleton with Factory + Cache

**Files:**
- Modify: `backend/app/services/mikrotik.py`

- [ ] **Step 1: Replace the singleton at the bottom of mikrotik.py**

Remove the last block (lines 239-247):
```python
# Singleton instance — falls back gracefully if MIKROTIK_* settings don't exist yet.
try:
    mikrotik = MikroTikClient()
except Exception:  # pragma: no cover
    mikrotik = MikroTikClient(  # type: ignore[assignment]
        url="https://192.168.88.1",
        user="admin",
        password="",
    )
```

Replace with:
```python
# --- Client Factory + Cache ---

_client_cache: dict[str, MikroTikClient] = {}


def get_mikrotik_client(
    router_id: str | None = None,
    url: str | None = None,
    user: str | None = None,
    password: str | None = None,
) -> MikroTikClient:
    """Get or create a MikroTikClient. Cached by router_id."""
    cache_key = router_id or "default"

    if cache_key in _client_cache:
        return _client_cache[cache_key]

    client = MikroTikClient(url=url, user=user, password=password)
    _client_cache[cache_key] = client
    return client


def invalidate_client(router_id: str) -> None:
    """Remove a cached client (call when router credentials change)."""
    _client_cache.pop(router_id, None)
    _client_cache.pop(str(router_id), None)


async def get_customer_router(db, customer):
    """Resolve the router for a customer: direct → area → first active."""
    from app.models.router import Router

    # 1. Direct assignment
    if customer.router_id:
        result = await db.execute(
            __import__('sqlalchemy').select(Router).where(Router.id == customer.router_id)
        )
        router = result.scalar_one_or_none()
        if router and router.is_active:
            return router

    # 2. Area's default router
    if customer.area and customer.area.router_id:
        result = await db.execute(
            __import__('sqlalchemy').select(Router).where(Router.id == customer.area.router_id)
        )
        router = result.scalar_one_or_none()
        if router and router.is_active:
            return router

    # 3. System default (first active router)
    from sqlalchemy import select
    result = await db.execute(
        select(Router).where(Router.is_active == True).order_by(Router.created_at).limit(1)
    )
    return result.scalar_one_or_none()


async def get_client_for_customer(db, customer) -> tuple[MikroTikClient | None, str | None]:
    """Resolve the customer's router and return (client, router_id)."""
    router = await get_customer_router(db, customer)
    if not router:
        logger.warning("No router found for customer %s", customer.id)
        return None, None

    client = get_mikrotik_client(
        router_id=str(router.id),
        url=router.url,
        user=router.username,
        password=router.password,
    )
    return client, str(router.id)


# Legacy singleton for backward compatibility (uses env vars)
mikrotik = get_mikrotik_client()
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/mikrotik.py
git commit -m "feat: replace MikroTik singleton with factory + cache + router resolution"
```

---

### Task 4: Router and Area API Routes

**Files:**
- Create: `backend/app/api/admin/routers.py`
- Create: `backend/app/api/admin/areas.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create Router CRUD API**

```python
# backend/app/api/admin/routers.py
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.router import Router
from app.models.user import User
from app.schemas.router import RouterCreate, RouterResponse, RouterStatusResponse, RouterUpdate
from app.services.mikrotik import MikroTikClient, get_mikrotik_client, invalidate_client

router = APIRouter(prefix="/routers", tags=["routers"])


@router.get("/", response_model=list[RouterResponse])
async def list_routers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Router).order_by(Router.created_at))
    return result.scalars().all()


@router.post("/", response_model=RouterResponse, status_code=status.HTTP_201_CREATED)
async def create_router(
    body: RouterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    r = Router(**body.model_dump())
    db.add(r)
    await db.flush()
    await db.refresh(r)
    return r


@router.get("/{router_id}", response_model=RouterResponse)
async def get_router(
    router_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Router).where(Router.id == router_id))
    r = result.scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="Router not found")
    return r


@router.put("/{router_id}", response_model=RouterResponse)
async def update_router(
    router_id: uuid.UUID,
    body: RouterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(Router).where(Router.id == router_id))
    r = result.scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="Router not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(r, field, value)

    invalidate_client(str(router_id))
    await db.flush()
    await db.refresh(r)
    return r


@router.delete("/{router_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_router(
    router_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(Router).where(Router.id == router_id))
    r = result.scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="Router not found")
    r.is_active = False
    invalidate_client(str(router_id))
    await db.flush()


@router.get("/{router_id}/status", response_model=RouterStatusResponse)
async def get_router_status(
    router_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Router).where(Router.id == router_id))
    r = result.scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="Router not found")

    client = get_mikrotik_client(str(r.id), r.url, r.username, r.password)
    try:
        identity = await client.get_identity()
        resources = await client.get_resources()
        sessions = await client.get_active_sessions()
        return RouterStatusResponse(
            id=r.id,
            name=r.name,
            connected=True,
            identity=identity,
            uptime=resources.get("uptime", ""),
            cpu_load=resources.get("cpu-load", "0"),
            free_memory=int(resources.get("free-memory", 0)),
            total_memory=int(resources.get("total-memory", 0)),
            active_sessions=len(sessions),
            version=resources.get("version", ""),
        )
    except Exception as e:
        return RouterStatusResponse(id=r.id, name=r.name, connected=False, error=str(e))
```

- [ ] **Step 2: Create Area CRUD API**

```python
# backend/app/api/admin/areas.py
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.router import Area
from app.models.user import User
from app.schemas.router import AreaCreate, AreaResponse, AreaUpdate

router = APIRouter(prefix="/areas", tags=["areas"])


@router.get("/", response_model=list[AreaResponse])
async def list_areas(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Area).order_by(Area.name))
    return result.scalars().all()


@router.post("/", response_model=AreaResponse, status_code=status.HTTP_201_CREATED)
async def create_area(
    body: AreaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    a = Area(**body.model_dump())
    db.add(a)
    await db.flush()
    await db.refresh(a)
    return a


@router.put("/{area_id}", response_model=AreaResponse)
async def update_area(
    area_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    body: AreaUpdate = None,
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(Area).where(Area.id == area_id))
    a = result.scalar_one_or_none()
    if a is None:
        raise HTTPException(status_code=404, detail="Area not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(a, field, value)

    await db.flush()
    await db.refresh(a)
    return a


@router.delete("/{area_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_area(
    area_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(Area).where(Area.id == area_id))
    a = result.scalar_one_or_none()
    if a is None:
        raise HTTPException(status_code=404, detail="Area not found")
    await db.delete(a)
    await db.flush()
```

- [ ] **Step 3: Register routers in main.py**

Add imports:
```python
from app.api.admin.routers import router as routers_router
from app.api.admin.areas import router as areas_router
```

Add registrations after billing_router:
```python
app.include_router(routers_router, prefix=settings.API_V1_PREFIX)
app.include_router(areas_router, prefix=settings.API_V1_PREFIX)
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/admin/routers.py backend/app/api/admin/areas.py backend/app/main.py
git commit -m "feat: add Router and Area CRUD API routes"
```

---

### Task 5: Wire Billing + Customers to Per-Router Client

**Files:**
- Modify: `backend/app/services/billing.py`
- Modify: `backend/app/api/admin/customers.py`

- [ ] **Step 1: Update billing.py**

In `record_payment`, replace all MikroTik blocks that use the singleton. The reconnect block currently reads:

```python
                if not skip_network:
                    if customer.mikrotik_secret_id:
                        from app.services.mikrotik import mikrotik
                        try:
                            await mikrotik.enable_secret(customer.mikrotik_secret_id)
                            ...
```

Replace every occurrence of this pattern with:
```python
                if not skip_network:
                    if customer.mikrotik_secret_id:
                        from app.services.mikrotik import get_client_for_customer
                        try:
                            client, _ = await get_client_for_customer(db, customer)
                            if client:
                                await client.enable_secret(customer.mikrotik_secret_id)
                                if customer.plan:
                                    profile_name = f"{customer.plan.download_mbps}M-{customer.plan.upload_mbps}M"
                                    rate_limit = f"{customer.plan.upload_mbps}M/{customer.plan.download_mbps}M"
                                    await client.ensure_profile(profile_name, rate_limit)
                                    await client.update_secret(customer.mikrotik_secret_id, {"profile": profile_name})
                        except Exception as e:
                            logger.error(f"MikroTik enable failed for {customer.id}: {e}")
                    else:
                        logger.warning(f"Customer {customer.id} has no mikrotik_secret_id, skipping")
```

In `process_graduated_disconnect`, the throttle block becomes:
```python
                if not skip_network:
                    if customer.mikrotik_secret_id:
                        from app.services.mikrotik import get_client_for_customer
                        try:
                            client, _ = await get_client_for_customer(db, customer)
                            if client:
                                throttle_name = f"{settings.THROTTLE_DOWNLOAD_MBPS}M-throttle"
                                throttle_rate = f"{settings.THROTTLE_UPLOAD_KBPS}k/{settings.THROTTLE_DOWNLOAD_MBPS}M"
                                await client.ensure_profile(throttle_name, throttle_rate)
                                await client.update_secret(customer.mikrotik_secret_id, {"profile": throttle_name})
                        except Exception as e:
                            logger.error(f"MikroTik throttle failed for {customer.id}: {e}")
                    else:
                        logger.warning(f"Customer {customer.id} has no mikrotik_secret_id, skipping")
```

The disconnect block becomes:
```python
                if not skip_network:
                    if customer.mikrotik_secret_id:
                        from app.services.mikrotik import get_client_for_customer
                        try:
                            client, _ = await get_client_for_customer(db, customer)
                            if client:
                                await client.disable_secret(customer.mikrotik_secret_id)
                        except Exception as e:
                            logger.error(f"MikroTik disconnect failed for {customer.id}: {e}")
                    else:
                        logger.warning(f"Customer {customer.id} has no mikrotik_secret_id, skipping")
```

- [ ] **Step 2: Update customers.py**

Replace all `from app.services.mikrotik import mikrotik` with `from app.services.mikrotik import get_client_for_customer, get_mikrotik_client`.

**create_customer** — resolve router, then provision:
```python
    # Auto-provision PPPoE secret on resolved router
    try:
        from app.services.mikrotik import get_client_for_customer
        client, _ = await get_client_for_customer(db, customer)
        if client:
            plan = customer.plan
            profile = "default"
            if plan:
                profile_name = f"{plan.download_mbps}M-{plan.upload_mbps}M"
                rate_limit = f"{plan.upload_mbps}M/{plan.download_mbps}M"
                profile = await client.ensure_profile(profile_name, rate_limit)

            secret_id = await client.create_secret(
                name=customer.pppoe_username,
                password=customer.pppoe_password,
                profile=profile,
                caller_id=customer.mac_address,
            )
            customer.mikrotik_secret_id = secret_id
            await db.flush()
            await db.refresh(customer)
    except Exception as e:
        logger.warning(f"MikroTik provisioning failed for {customer.id}: {e}")
```

**disconnect_customer**, **reconnect_customer**, **throttle_customer** — same pattern: resolve client via `get_client_for_customer(db, customer)` then call methods on the client instead of the `mikrotik` singleton.

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/billing.py backend/app/api/admin/customers.py
git commit -m "feat: wire billing and customers to per-router MikroTik client"
```

---

### Task 6: Update Network API (Dashboard, Import, Sessions) for Multi-Router

**Files:**
- Modify: `backend/app/api/admin/network.py`
- Modify: `backend/app/api/admin/plans.py`

- [ ] **Step 1: Update dashboard endpoint**

In the dashboard endpoint in `network.py`, replace the single-router MikroTik stats section with a loop over all active routers:

```python
    # --- MikroTik Live Stats (all active routers) ---
    from app.models.router import Router
    routers_result = await db.execute(select(Router).where(Router.is_active == True))
    all_routers = routers_result.scalars().all()

    import asyncio
    router_stats = []
    total_sessions = 0

    async def fetch_router_stats(r):
        client = get_mikrotik_client(str(r.id), r.url, r.username, r.password)
        try:
            identity = await client.get_identity()
            resources = await client.get_resources()
            sessions = await client.get_active_sessions()
            interfaces_resp = await client._request("GET", "interface")
            interfaces = [
                {
                    "name": i.get("name", ""),
                    "type": i.get("type", ""),
                    "running": i.get("running", "false") == "true",
                    "rx_bytes": int(i.get("rx-byte", 0)),
                    "tx_bytes": int(i.get("tx-byte", 0)),
                }
                for i in interfaces_resp.json()
                if i.get("type") in ("ether", "pppoe-in")
            ]
            return {
                "id": str(r.id),
                "name": r.name,
                "location": r.location,
                "connected": True,
                "identity": identity,
                "uptime": resources.get("uptime", ""),
                "cpu_load": resources.get("cpu-load", "0"),
                "free_memory": int(resources.get("free-memory", 0)),
                "total_memory": int(resources.get("total-memory", 0)),
                "active_sessions": len(sessions),
                "version": resources.get("version", ""),
                "interfaces": interfaces,
            }
        except Exception as e:
            return {
                "id": str(r.id),
                "name": r.name,
                "location": r.location,
                "connected": False,
                "error": str(e),
                "active_sessions": 0,
            }

    if all_routers:
        router_stats = await asyncio.gather(*[fetch_router_stats(r) for r in all_routers])
        total_sessions = sum(rs.get("active_sessions", 0) for rs in router_stats)

    # Replace the old single mt_stats with:
    # "mikrotik": {"routers": router_stats, "total_sessions": total_sessions}
```

Update the return to include `routers` array instead of single `mikrotik` object.

- [ ] **Step 2: Update active-sessions and subscribers to accept router_id filter**

```python
@router.get("/active-sessions")
async def get_active_sessions(
    router_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.router import Router
    if router_id:
        result = await db.execute(select(Router).where(Router.id == router_id))
        r = result.scalar_one_or_none()
        if not r:
            return {"sessions": [], "total": 0, "error": "Router not found"}
        client = get_mikrotik_client(str(r.id), r.url, r.username, r.password)
    else:
        # Aggregate from all active routers
        ...
```

- [ ] **Step 3: Update plans.py to sync profiles across all active routers**

In the plan update endpoint, replace the single-router profile sync with a loop:

```python
    if plan.download_mbps != old_download or plan.upload_mbps != old_upload:
        from app.models.router import Router
        routers_result = await db.execute(select(Router).where(Router.is_active == True))
        for r in routers_result.scalars().all():
            try:
                client = get_mikrotik_client(str(r.id), r.url, r.username, r.password)
                # ... sync profile on each router
```

- [ ] **Step 4: Move import endpoint to routers.py as /routers/{id}/import**

Move the `POST /network/import` logic into `routers.py` as `POST /routers/{router_id}/import`, using the specific router's client.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/admin/network.py backend/app/api/admin/plans.py backend/app/api/admin/routers.py
git commit -m "feat: multi-router dashboard, filtered sessions, per-router import"
```

---

### Task 7: Frontend — Routers and Areas Pages

**Files:**
- Create: `frontend/src/api/routers.ts`
- Create: `frontend/src/pages/Routers.tsx`
- Create: `frontend/src/pages/Areas.tsx`
- Modify: `frontend/src/components/Layout/SideMenu.tsx`

- [ ] **Step 1: Create routers API client**

```typescript
// frontend/src/api/routers.ts
import client from './client';

export interface RouterType {
  id: string;
  name: string;
  url: string;
  username: string;
  location: string | null;
  is_active: boolean;
  created_at: string;
}

export interface RouterStatus {
  id: string;
  name: string;
  connected: boolean;
  identity?: string;
  uptime?: string;
  cpu_load?: string;
  active_sessions?: number;
  version?: string;
  error?: string;
}

export interface AreaType {
  id: string;
  name: string;
  description: string | null;
  router_id: string | null;
  router: RouterType | null;
  created_at: string;
}

export const getRouters = () => client.get<RouterType[]>('/routers/');
export const createRouter = (data: any) => client.post<RouterType>('/routers/', data);
export const updateRouter = (id: string, data: any) => client.put<RouterType>(`/routers/${id}`, data);
export const deleteRouter = (id: string) => client.delete(`/routers/${id}`);
export const getRouterStatus = (id: string) => client.get<RouterStatus>(`/routers/${id}/status`);
export const importFromRouter = (id: string) => client.post(`/routers/${id}/import`);

export const getAreas = () => client.get<AreaType[]>('/areas/');
export const createArea = (data: any) => client.post<AreaType>('/areas/', data);
export const updateArea = (id: string, data: any) => client.put<AreaType>(`/areas/${id}`, data);
export const deleteArea = (id: string) => client.delete(`/areas/${id}`);
```

- [ ] **Step 2: Create Routers page**

Create `frontend/src/pages/Routers.tsx` with:
- Table showing all routers (name, URL, location, status badge, sessions count)
- Add/Edit modal (name, URL, username, password, location)
- "Test Connection" button that calls `getRouterStatus`
- "Import Subscribers" button that calls `importFromRouter`
- Status badges with auto-refresh (green=connected, red=disconnected)

- [ ] **Step 3: Create Areas page**

Create `frontend/src/pages/Areas.tsx` with:
- Table showing all areas (name, description, assigned router name)
- Add/Edit modal (name, description, router dropdown)

- [ ] **Step 4: Update SideMenu**

Add to `frontend/src/components/Layout/SideMenu.tsx`:
```typescript
{ key: '/routers', icon: <CloudServerOutlined />, label: 'Routers' },
{ key: '/areas', icon: <EnvironmentOutlined />, label: 'Areas' },
```

Add the icons to imports:
```typescript
import { ..., CloudServerOutlined, EnvironmentOutlined } from '@ant-design/icons';
```

- [ ] **Step 5: Add routes in App**

Register routes for `/routers` and `/areas` in the router configuration (same file that has the other route definitions).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api/routers.ts frontend/src/pages/Routers.tsx frontend/src/pages/Areas.tsx frontend/src/components/Layout/SideMenu.tsx
git commit -m "feat: Routers and Areas management pages"
```

---

### Task 8: Frontend — Update Dashboard and Active Users for Multi-Router

**Files:**
- Modify: `frontend/src/pages/Dashboard.tsx`
- Modify: `frontend/src/pages/ActiveUsers.tsx`
- Modify: `frontend/src/api/network.ts`

- [ ] **Step 1: Update DashboardData type**

In `frontend/src/api/network.ts`, update the `mikrotik` field in `DashboardData`:

```typescript
  mikrotik: {
    total_sessions: number;
    routers: Array<{
      id: string;
      name: string;
      location: string | null;
      connected: boolean;
      identity?: string;
      uptime?: string;
      cpu_load?: string;
      free_memory?: number;
      total_memory?: number;
      active_sessions?: number;
      version?: string;
      error?: string;
      interfaces?: Array<{
        name: string;
        type: string;
        running: boolean;
        rx_bytes: number;
        tx_bytes: number;
      }>;
    }>;
  };
```

- [ ] **Step 2: Update Dashboard to show per-router health cards**

Replace the single MikroTik health card with a scrollable row of router cards:

```tsx
{mt.routers?.map((r) => (
  <Col key={r.id} xs={24} lg={12}>
    <Card title={<Space><CloudServerOutlined /> {r.name} <Tag color={r.connected ? 'green' : 'red'}>{r.connected ? 'Online' : 'Offline'}</Tag></Space>}>
      {/* CPU gauge, memory gauge, sessions, uptime per router */}
    </Card>
  </Col>
))}
```

- [ ] **Step 3: Update Active Users with router filter**

Add a `Select` dropdown at the top of ActiveUsers.tsx to filter by router. Pass `?router_id=` to the API.

```tsx
const [routerFilter, setRouterFilter] = useState<string | undefined>();
// Add Select with router list
// Pass routerFilter to getActiveSessions query
```

- [ ] **Step 4: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Dashboard.tsx frontend/src/pages/ActiveUsers.tsx frontend/src/api/network.ts
git commit -m "feat: per-router dashboard health cards and session filtering"
```
