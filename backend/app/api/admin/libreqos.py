import secrets
import uuid
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.tenant import get_tenant_id
from app.models.app_setting import AppSetting
from app.models.customer import Customer, CustomerStatus
from app.models.router import Router
from app.models.user import User
from app.services.mikrotik import get_mikrotik_client

router = APIRouter(tags=["libreqos"])


@router.post("/settings/libreqos/token")
async def generate_libreqos_token(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Generate or regenerate a LibreQoS API token for this tenant."""
    tid = uuid.UUID(tenant_id)
    token = secrets.token_urlsafe(32)

    result = await db.execute(
        select(AppSetting).where(AppSetting.key == "libreqos_token", AppSetting.owner_id == tid)
    )
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = token
    else:
        db.add(AppSetting(key="libreqos_token", value=token, owner_id=tid))
    await db.flush()
    return {"token": token}


@router.get("/settings/libreqos")
async def get_libreqos_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Get LibreQoS integration settings."""
    tid = uuid.UUID(tenant_id)
    result = await db.execute(
        select(AppSetting).where(AppSetting.key == "libreqos_token", AppSetting.owner_id == tid)
    )
    setting = result.scalar_one_or_none()
    return {"token": setting.value if setting else None}


@router.get("/libreqos/shaped-devices.csv")
async def shaped_devices_csv(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint: returns ShapedDevices.csv for LibreQoS.
    Authenticated by tenant API token, no session/JWT needed.
    """
    # Resolve tenant from token
    result = await db.execute(
        select(AppSetting).where(AppSetting.key == "libreqos_token", AppSetting.value == token)
    )
    setting = result.scalar_one_or_none()
    if not setting:
        raise HTTPException(status_code=401, detail="Invalid token")
    tid = setting.owner_id

    # Get active customers with plans
    cust_result = await db.execute(
        select(Customer).where(
            Customer.owner_id == tid,
            Customer.status == CustomerStatus.active,
            Customer.plan_id.isnot(None),
        )
    )
    customers = cust_result.scalars().all()

    # Get active PPPoE sessions from all tenant routers for IP mapping
    router_result = await db.execute(
        select(Router).where(Router.owner_id == tid, Router.is_active == True)
    )
    routers = router_result.scalars().all()

    ip_map: dict[str, str] = {}  # pppoe_username -> ip_address
    mac_map: dict[str, str] = {}  # pppoe_username -> mac_address
    for r in routers:
        try:
            client = get_mikrotik_client(str(r.id), r.url, r.username, r.password)
            sessions = await client.get_active_sessions()
            for s in sessions:
                name = s.get("name", "")
                if name:
                    ip_map[name] = s.get("address", "")
                    mac_map[name] = s.get("caller-id", "")
        except Exception:
            pass

    # Build CSV
    buf = StringIO()
    buf.write("Circuit ID,Circuit Name,Device ID,Device Name,Parent Node,MAC,IPv4,IPv6,Download Min,Upload Min,Download Max,Upload Max,Comment\n")

    for c in customers:
        plan = c.plan
        if not plan:
            continue
        ip = ip_map.get(c.pppoe_username, "")
        mac = mac_map.get(c.pppoe_username, "")
        if not ip:
            continue  # Skip offline customers — LibreQoS can't shape without an IP

        download_max = plan.download_mbps
        upload_max = plan.upload_mbps
        # Min = 30% of max as reasonable floor
        download_min = max(1, int(download_max * 0.3))
        upload_min = max(1, int(upload_max * 0.3))

        buf.write(
            f"{c.id},{c.full_name},{c.id},{c.pppoe_username},,{mac},{ip},,"
            f"{download_min},{upload_min},{download_max},{upload_max},"
            f"{plan.name}\n"
        )

    return PlainTextResponse(content=buf.getvalue(), media_type="text/csv")
