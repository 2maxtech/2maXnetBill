import asyncio
import logging

from app.celery_app import celery
from app.core.config import settings

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    try:
        asyncio.get_running_loop()
        # If there's already a loop (shouldn't happen in Celery), use it
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
        return asyncio.run(coro)


@celery.task(name="app.tasks.billing.generate_monthly_invoices_task")
def generate_monthly_invoices_task():
    """Generate monthly invoices for all active customers. Runs on 1st of month."""
    from app.services.billing import generate_monthly_invoices
    from app.core.database import async_session

    async def _run():
        async with async_session() as db:
            try:
                result = await generate_monthly_invoices(db)
                await db.commit()
                logger.info(f"Monthly invoices: generated={result['generated']}, skipped={result['skipped']}")
                return result
            except Exception:
                await db.rollback()
                raise

    return _run_async(_run())


@celery.task(name="app.tasks.billing.check_overdue_invoices_task")
def check_overdue_invoices_task():
    """Check for overdue invoices and mark them. Runs daily."""
    from app.services.billing import check_overdue_invoices
    from app.core.database import async_session

    async def _run():
        async with async_session() as db:
            try:
                count = await check_overdue_invoices(db)
                await db.commit()
                logger.info(f"Overdue invoices marked: {count}")
                return {"marked_overdue": count}
            except Exception:
                await db.rollback()
                raise

    return _run_async(_run())


@celery.task(name="app.tasks.billing.process_graduated_disconnect_task")
def process_graduated_disconnect_task():
    """Process graduated disconnect enforcement. Runs daily."""
    from app.services.billing import process_graduated_disconnect
    from app.core.database import async_session

    async def _run():
        async with async_session() as db:
            try:
                result = await process_graduated_disconnect(db)
                await db.commit()
                logger.info(f"Graduated disconnect: {result}")
                return result
            except Exception:
                await db.rollback()
                raise

    return _run_async(_run())


@celery.task(name="app.tasks.billing.send_billing_reminders_task")
def send_billing_reminders_task():
    """Send billing reminders. Runs daily."""
    from app.services.billing import send_billing_reminders
    from app.core.database import async_session

    async def _run():
        async with async_session() as db:
            try:
                count = await send_billing_reminders(db)
                await db.commit()
                logger.info(f"Billing reminders sent: {count}")
                return {"reminders_sent": count}
            except Exception:
                await db.rollback()
                raise

    return _run_async(_run())


@celery.task(name="app.tasks.billing.process_notifications_task")
def process_notifications_task():
    """Process and send pending notifications. Runs every 5 minutes."""
    import asyncio
    from app.services.notification import process_pending_notifications
    from app.core.database import async_session

    async def _run():
        async with async_session() as db:
            try:
                result = await process_pending_notifications(db)
                await db.commit()
                logger.info(f"Notifications processed: {result}")
                return result
            except Exception:
                await db.rollback()
                raise

    return _run_async(_run())
