import logging
import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.app_setting import AppSetting

logger = logging.getLogger(__name__)


async def get_sms_settings(db: AsyncSession, tenant_id: uuid.UUID | None = None) -> dict:
    query = select(AppSetting).where(AppSetting.key.like("sms_%"))
    if tenant_id is not None:
        query = query.where(AppSetting.owner_id == tenant_id)
    else:
        query = query.where(AppSetting.owner_id.is_(None))
    result = await db.execute(query)
    settings = {s.key: s.value for s in result.scalars().all()}
    return settings


async def send_sms(phone: str, message: str, db: AsyncSession, tenant_id: uuid.UUID | None = None) -> bool:
    settings = await get_sms_settings(db, tenant_id=tenant_id)
    provider = settings.get("sms_provider", "")
    api_key = settings.get("sms_api_key", "")

    if not provider or not api_key:
        logger.warning("SMS not configured, skipping")
        return False

    if provider == "semaphore":
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "https://api.semaphore.co/api/v4/messages",
                    json={
                        "apikey": api_key,
                        "number": phone,
                        "message": message,
                        "sendername": settings.get("sms_sender_name", "NetLedger"),
                    },
                )
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"SMS send failed: {e}")
            return False

    logger.warning(f"Unknown SMS provider: {provider}")
    return False
