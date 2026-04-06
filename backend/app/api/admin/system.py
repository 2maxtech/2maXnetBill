import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.app_setting import AppSetting
from app.models.user import User

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/update-check")
async def check_update(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get available update info (on-premise only)."""
    if settings.DEPLOYMENT_MODE != "onpremise":
        return {"update_available": False}

    result = await db.execute(
        select(AppSetting).where(
            AppSetting.key == "update_available",
            AppSetting.owner_id.is_(None),
        )
    )
    setting = result.scalar_one_or_none()
    if setting and setting.value:
        info = json.loads(setting.value)
        return {"update_available": True, **info}
    return {"update_available": False}


@router.get("/version")
async def get_version():
    """Get current app version and deployment mode (public)."""
    return {
        "version": settings.APP_VERSION,
        "deployment_mode": settings.DEPLOYMENT_MODE,
    }
