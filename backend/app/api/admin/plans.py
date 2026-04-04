import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.plan import Plan
from app.models.user import User
from app.schemas.plan import PlanCreate, PlanResponse, PlanUpdate
from app.services.mikrotik import mikrotik

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("/", response_model=list[PlanResponse])
async def list_plans(
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Plan)
    if active_only:
        query = query.where(Plan.is_active == True)
    query = query.order_by(Plan.monthly_price)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    body: PlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = Plan(**body.model_dump())
    db.add(plan)
    await db.flush()
    await db.refresh(plan)
    return plan


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.put("/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: uuid.UUID,
    body: PlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    old_download = plan.download_mbps
    old_upload = plan.upload_mbps

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)

    await db.flush()
    await db.refresh(plan)

    # Sync to MikroTik if speeds changed
    if plan.download_mbps != old_download or plan.upload_mbps != old_upload:
        try:
            old_profile = f"{old_download}M-{old_upload}M"
            new_profile = f"{plan.download_mbps}M-{plan.upload_mbps}M"
            new_rate = f"{plan.upload_mbps}M/{plan.download_mbps}M"
            await mikrotik.ensure_profile(new_profile, new_rate)

            # Update all secrets using the old profile to the new one
            secrets = await mikrotik.get_secrets()
            for s in secrets:
                if s.get("profile") == old_profile:
                    await mikrotik.update_secret(s[".id"], {"profile": new_profile})
            logger.info(f"Plan '{plan.name}' synced to MikroTik: {old_profile} → {new_profile}")
        except Exception as e:
            logger.warning(f"MikroTik profile sync failed for plan {plan.id}: {e}")

    return plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan.is_active = False
    await db.flush()
