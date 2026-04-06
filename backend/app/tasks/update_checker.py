import asyncio
import json
import logging

from app.celery_app import celery

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    try:
        asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
        return asyncio.run(coro)


@celery.task(name="app.tasks.update_checker.check_updates_task")
def check_updates_task():
    """Daily task to check for updates (on-premise only)."""
    _run_async(_check_updates())


async def _check_updates():
    from app.core.database import async_session
    from app.models.app_setting import AppSetting
    from app.services.update_checker import check_for_updates
    from sqlalchemy import select

    update_info = await check_for_updates()
    async with async_session() as session:
        try:
            result = await session.execute(
                select(AppSetting).where(
                    AppSetting.key == "update_available",
                    AppSetting.owner_id.is_(None),
                )
            )
            existing = result.scalar_one_or_none()

            if update_info:
                value = json.dumps(update_info)
                if existing:
                    existing.value = value
                else:
                    session.add(AppSetting(key="update_available", value=value, owner_id=None))
            else:
                if existing:
                    await session.delete(existing)

            await session.commit()
            if update_info:
                logger.info(f"Update available: v{update_info['version']}")
            else:
                logger.info("No updates available")
        except Exception:
            await session.rollback()
            raise
