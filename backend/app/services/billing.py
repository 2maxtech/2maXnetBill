import logging
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import and_, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.customer import Customer, CustomerStatus
from app.models.disconnect_log import DisconnectAction, DisconnectLog, DisconnectReason
from app.models.invoice import Invoice, InvoiceStatus
from app.models.notification import Notification, NotificationStatus, NotificationType
from app.models.payment import Payment

logger = logging.getLogger(__name__)


async def generate_invoice(db: AsyncSession, customer: Customer, billing_period: date) -> Invoice:
    """Generate an invoice for a customer. Idempotent — skips if one already exists for the period."""
    result = await db.execute(
        select(Invoice).where(
            and_(
                Invoice.customer_id == customer.id,
                extract("year", Invoice.issued_at) == billing_period.year,
                extract("month", Invoice.issued_at) == billing_period.month,
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    plan = customer.plan
    due_day = min(settings.BILLING_DUE_DAY, 28)
    due_date = billing_period.replace(day=due_day)

    invoice = Invoice(
        customer_id=customer.id,
        plan_id=plan.id,
        amount=plan.monthly_price,
        due_date=due_date,
        status=InvoiceStatus.pending,
        issued_at=datetime.now(timezone.utc),
    )
    db.add(invoice)
    await db.flush()
    await db.refresh(invoice)
    return invoice


async def generate_monthly_invoices(db: AsyncSession) -> dict:
    """Generate invoices for all active/suspended customers for the current month."""
    today = date.today()
    billing_period = today.replace(day=1)

    result = await db.execute(
        select(Customer).where(
            Customer.status.in_([CustomerStatus.active, CustomerStatus.suspended]),
            Customer.plan_id.isnot(None),
        )
    )
    customers = result.scalars().all()

    generated = 0
    skipped = 0
    errors = []

    for cust in customers:
        try:
            existing = await db.execute(
                select(Invoice).where(
                    and_(
                        Invoice.customer_id == cust.id,
                        extract("year", Invoice.issued_at) == billing_period.year,
                        extract("month", Invoice.issued_at) == billing_period.month,
                    )
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            await generate_invoice(db, cust, billing_period)
            generated += 1
        except Exception as e:
            logger.error(f"Failed to generate invoice for customer {cust.id}: {e}")
            errors.append({"customer_id": str(cust.id), "error": str(e)})

    return {"generated": generated, "skipped": skipped, "errors": errors}
