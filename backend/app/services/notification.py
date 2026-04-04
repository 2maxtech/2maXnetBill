import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.customer import Customer
from app.models.notification import Notification, NotificationStatus, NotificationType

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, body: str) -> bool:
    """Send email via SMTP. Returns False if SMTP not configured."""
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.warning("SMTP not configured, skipping email send")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent to {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Email send failed to {to}: {e}")
        return False


async def process_pending_notifications(db: AsyncSession) -> dict:
    """Process all pending notifications — send emails and update status."""
    result = await db.execute(
        select(Notification).where(Notification.status == NotificationStatus.pending)
    )
    notifications = result.scalars().all()

    sent = 0
    failed = 0
    skipped = 0

    for notif in notifications:
        cust_result = await db.execute(
            select(Customer).where(Customer.id == notif.customer_id)
        )
        customer = cust_result.scalar_one_or_none()

        if not customer:
            notif.status = NotificationStatus.failed
            failed += 1
            continue

        # Only process email notifications; skip SMS for now
        if notif.type == NotificationType.sms:
            skipped += 1
            continue

        success = await send_email(customer.email, notif.subject, notif.message)

        if success:
            notif.status = NotificationStatus.sent
            notif.sent_at = datetime.now(timezone.utc)
            sent += 1
        else:
            notif.status = NotificationStatus.failed
            failed += 1

    await db.flush()
    return {"sent": sent, "failed": failed, "skipped": skipped}
