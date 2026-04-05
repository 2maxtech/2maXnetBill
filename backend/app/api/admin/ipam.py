import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.tenant import get_tenant_id
from app.models.ip_pool import IPPool
from app.models.user import User

router = APIRouter(prefix="/ipam", tags=["ipam"])


class IPPoolCreate(BaseModel):
    name: str
    router_id: uuid.UUID
    range_start: str
    range_end: str
    subnet: str


class IPPoolResponse(BaseModel):
    id: uuid.UUID
    name: str
    router_id: uuid.UUID
    range_start: str
    range_end: str
    subnet: str

    model_config = {"from_attributes": True}


@router.get("/pools", response_model=list[IPPoolResponse])
async def list_pools(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """List all IP pools with router info."""
    tid = uuid.UUID(tenant_id)
    result = await db.execute(select(IPPool).where(IPPool.owner_id == tid).order_by(IPPool.name))
    return result.scalars().all()


@router.post("/pools", response_model=IPPoolResponse, status_code=status.HTTP_201_CREATED)
async def create_pool(
    body: IPPoolCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Create a new IP pool."""
    pool = IPPool(**body.model_dump())
    pool.owner_id = uuid.UUID(tenant_id)
    db.add(pool)
    await db.flush()
    await db.refresh(pool)
    return pool


@router.put("/pools/{pool_id}")
async def update_pool(
    pool_id: uuid.UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Update an existing IP pool."""
    tid = uuid.UUID(tenant_id)
    result = await db.execute(select(IPPool).where(IPPool.id == pool_id, IPPool.owner_id == tid))
    pool = result.scalar_one_or_none()
    if pool is None:
        raise HTTPException(status_code=404, detail="Pool not found")
    for field in ["name", "range_start", "range_end", "subnet", "router_id"]:
        if field in body:
            setattr(pool, field, body[field])
    await db.flush()
    await db.refresh(pool)
    return {
        "id": str(pool.id),
        "name": pool.name,
        "range_start": pool.range_start,
        "range_end": pool.range_end,
        "subnet": pool.subnet,
    }


@router.delete("/pools/{pool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pool(
    pool_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Delete an IP pool."""
    tid = uuid.UUID(tenant_id)
    result = await db.execute(select(IPPool).where(IPPool.id == pool_id, IPPool.owner_id == tid))
    pool = result.scalar_one_or_none()
    if pool is None:
        raise HTTPException(status_code=404, detail="IP pool not found")

    await db.delete(pool)
    await db.flush()
