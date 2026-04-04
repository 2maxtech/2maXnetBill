import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.customer import Customer, CustomerStatus
from app.models.plan import Plan
from app.models.router import Router
from app.models.user import User
from app.schemas.router import RouterCreate, RouterResponse, RouterStatusResponse, RouterUpdate
from app.services.mikrotik import get_mikrotik_client, invalidate_client

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


@router.post("/{router_id}/import")
async def import_from_router(
    router_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Import PPPoE secrets and profiles from a specific router into NetLedger."""
    result = await db.execute(select(Router).where(Router.id == router_id))
    r = result.scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="Router not found")

    client = get_mikrotik_client(str(r.id), r.url, r.username, r.password)

    try:
        mt_profiles = await client.get_profiles()
        mt_secrets = await client.get_secrets()
    except Exception as e:
        return {"error": f"Failed to connect: {e}"}

    # Build profile → rate-limit map
    profile_rates: dict[str, str] = {}
    for p in mt_profiles:
        if p.get("rate-limit"):
            profile_rates[p["name"]] = p["rate-limit"]

    # Get existing customers to skip duplicates
    existing_result = await db.execute(select(Customer))
    existing_customers = existing_result.scalars().all()
    existing_usernames = {c.pppoe_username for c in existing_customers}
    existing_secret_ids = {c.mikrotik_secret_id for c in existing_customers if c.mikrotik_secret_id}

    # Get existing plans
    plans_result = await db.execute(select(Plan))
    existing_plans_list = plans_result.scalars().all()
    existing_plans = {p.name: p for p in existing_plans_list}

    def _to_mbps(s: str) -> int:
        s = s.strip().lower()
        if s.endswith("m"):
            return int(float(s[:-1]))
        elif s.endswith("k"):
            return max(1, int(float(s[:-1]) / 1000))
        return max(1, int(float(s)) // 1_000_000) if s.replace(".", "").isdigit() else 1

    plans_created = 0
    customers_created = 0
    customers_skipped = 0

    # Create plans from profiles
    plan_map: dict[str, Plan] = {}
    for pname, rate in profile_rates.items():
        if pname in existing_plans:
            plan_map[pname] = existing_plans[pname]
            continue
        parts = rate.split("/")
        if len(parts) == 2:
            download = _to_mbps(parts[1])
            upload = _to_mbps(parts[0])
        else:
            download, upload = 10, 5
        plan = Plan(
            name=pname,
            download_mbps=download,
            upload_mbps=upload,
            monthly_price=Decimal("0.00"),
            is_active=True,
            description=f"Imported from MikroTik",
        )
        db.add(plan)
        await db.flush()
        await db.refresh(plan)
        plan_map[pname] = plan
        existing_plans[pname] = plan
        plans_created += 1

    # Create customers from secrets
    for secret in mt_secrets:
        secret_id = secret.get(".id", "")
        username = secret.get("name", "")
        if not username:
            continue
        if username in existing_usernames or secret_id in existing_secret_ids:
            customers_skipped += 1
            continue
        profile = secret.get("profile", "default")
        plan = plan_map.get(profile)
        if not plan:
            plan = next((p for p in existing_plans.values() if p.is_active), None)
        if not plan:
            customers_skipped += 1
            continue
        customer = Customer(
            full_name=username.replace(".", " ").replace("_", " ").title(),
            email=f"{username}@imported.local",
            phone="0000000000",
            pppoe_username=username,
            pppoe_password=secret.get("password", "imported"),
            status=CustomerStatus.disconnected if secret.get("disabled") == "true" else CustomerStatus.active,
            plan_id=plan.id,
            mikrotik_secret_id=secret_id,
            mac_address=secret.get("caller-id") or None,
            router_id=router_id,
        )
        db.add(customer)
        existing_usernames.add(username)
        customers_created += 1

    await db.flush()
    return {
        "plans_created": plans_created,
        "customers_created": customers_created,
        "customers_skipped": customers_skipped,
        "total_secrets": len(mt_secrets),
    }
