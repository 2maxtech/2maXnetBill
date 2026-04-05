import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.app_setting import AppSetting
from app.models.customer import Customer
from app.models.notification import Notification, NotificationStatus, NotificationType

logger = logging.getLogger(__name__)


async def _get_tenant_smtp(db: AsyncSession, tenant_id) -> dict:
    """Get SMTP settings for a tenant, falling back to global config."""
    if tenant_id:
        result = await db.execute(
            select(AppSetting).where(AppSetting.key.like("smtp_%"), AppSetting.owner_id == tenant_id)
        )
        tenant_smtp = {s.key: s.value for s in result.scalars().all()}
        if tenant_smtp.get("smtp_host"):
            return tenant_smtp
    # Fall back to global env settings
    return {
        "smtp_host": settings.SMTP_HOST,
        "smtp_port": str(settings.SMTP_PORT),
        "smtp_user": settings.SMTP_USER,
        "smtp_password": settings.SMTP_PASSWORD,
        "smtp_from": settings.SMTP_FROM,
        "smtp_from_name": getattr(settings, "SMTP_FROM_NAME", "NetLedger"),
    }


async def send_email_tenant(db: AsyncSession, tenant_id, to: str, subject: str, body: str, html: str | None = None, pdf_bytes: bytes | None = None, pdf_name: str | None = None) -> bool:
    """Send email using tenant's SMTP settings."""
    smtp_cfg = await _get_tenant_smtp(db, tenant_id)
    host = smtp_cfg.get("smtp_host", "")
    if not host:
        logger.warning("SMTP not configured, skipping email send")
        return False

    port = int(smtp_cfg.get("smtp_port", 587))
    user = smtp_cfg.get("smtp_user", "")
    password = smtp_cfg.get("smtp_password", "")
    from_addr = smtp_cfg.get("smtp_from", user)
    from_name = smtp_cfg.get("smtp_from_name", "NetLedger")

    try:
        msg = MIMEMultipart()
        msg["From"] = f"{from_name} <{from_addr}>"
        msg["To"] = to
        msg["Subject"] = subject

        if html:
            msg.attach(MIMEText(html, "html"))
        else:
            msg.attach(MIMEText(body, "plain"))

        if pdf_bytes and pdf_name:
            pdf_part = MIMEApplication(pdf_bytes, _subtype="pdf")
            pdf_part.add_header("Content-Disposition", "attachment", filename=pdf_name)
            msg.attach(pdf_part)

        with smtplib.SMTP(host, port, timeout=15) as server:
            server.ehlo()
            if port != 465:
                server.starttls()
            if user and password:
                server.login(user, password)
            server.sendmail(from_addr, [to], msg.as_string())

        logger.info(f"Email sent to {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Email send failed to {to}: {e}")
        return False


async def send_email(to: str, subject: str, body: str) -> bool:
    """Legacy: Send email via global SMTP config."""
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
    """Process all pending notifications — send emails and SMS."""
    from app.services.sms import send_sms

    result = await db.execute(
        select(Notification).where(Notification.status == NotificationStatus.pending).limit(50)
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

        if notif.type == NotificationType.sms:
            if not customer.phone or customer.phone == "0000000000":
                notif.status = NotificationStatus.failed
                failed += 1
                continue
            success = await send_sms(customer.phone, notif.message, db, tenant_id=notif.owner_id)
        elif notif.type == NotificationType.email:
            if not customer.email or customer.email.endswith("@imported.local"):
                notif.status = NotificationStatus.failed
                failed += 1
                continue
            success = await send_email_tenant(db, notif.owner_id, customer.email, notif.subject, notif.message)
        else:
            skipped += 1
            continue

        if success:
            notif.status = NotificationStatus.sent
            notif.sent_at = datetime.now(timezone.utc)
            sent += 1
        else:
            notif.status = NotificationStatus.failed
            failed += 1

    await db.flush()
    return {"sent": sent, "failed": failed, "skipped": skipped}
