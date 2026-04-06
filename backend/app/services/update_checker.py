import logging
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def check_for_updates() -> dict | None:
    """Check if a newer version is available. Returns info dict or None."""
    if settings.DEPLOYMENT_MODE != "onpremise":
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(settings.UPDATE_CHECK_URL)
            if resp.status_code != 200:
                return None
            data = resp.json()
            latest = data.get("version", "")
            if not latest:
                return None
            # Simple version comparison
            current_parts = [int(x) for x in settings.APP_VERSION.split(".")]
            latest_parts = [int(x) for x in latest.split(".")]
            if latest_parts > current_parts:
                return {
                    "version": latest,
                    "release_notes": data.get("release_notes", ""),
                    "release_date": data.get("release_date", ""),
                    "download_url": data.get("download_url", ""),
                }
    except Exception as e:
        logger.warning(f"Update check failed: {e}")
    return None
