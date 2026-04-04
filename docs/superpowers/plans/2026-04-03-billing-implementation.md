# Billing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement billing engine — invoice generation, payment recording with auto-reconnect, graduated disconnect enforcement via Celery, and wire up the frontend.

**Architecture:** Billing service layer (pure logic) called by both FastAPI endpoints and Celery tasks. Celery worker + Beat as separate Docker containers using the same backend image. Sync SQLAlchemy sessions in Celery tasks (psycopg2), async sessions in FastAPI (asyncpg).

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Celery 5.4, Redis, PostgreSQL, React 18, Ant Design 5, React Query

---

### Task 1: Add psycopg2-binary + Celery App Setup

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/app/celery_app.py`
- Create: `backend/app/tasks/__init__.py`

- [ ] **Step 1: Add psycopg2-binary to requirements.txt**

Add after `asyncpg==0.30.0`:

```
psycopg2-binary==2.9.10
```

- [ ] **Step 2: Create Celery app**

Create `backend/app/celery_app.py`:

```python
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery = Celery(
    "netbill",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.billing"],
)

celery.conf.beat_schedule = {
    "generate-monthly-invoices": {
        "task": "app.tasks.billing.generate_monthly_invoices_task",
        "schedule": crontab(day_of_month=str(settings.BILLING_GENERATE_DAY), hour="2", minute="0"),
    },
    "check-overdue-invoices": {
        "task": "app.tasks.billing.check_overdue_invoices_task",
        "schedule": crontab(hour="6", minute="0"),
    },
    "process-graduated-disconnect": {
        "task": "app.tasks.billing.process_graduated_disconnect_task",
        "schedule": crontab(hour="7", minute="0"),
    },
    "send-billing-reminders": {
        "task": "app.tasks.billing.send_billing_reminders_task",
        "schedule": crontab(hour="9", minute="0"),
    },
}

celery.conf.timezone = "Asia/Manila"
```

- [ ] **Step 3: Create tasks package**

Create `backend/app/tasks/__init__.py` (empty file).

- [ ] **Step 4: Commit**

```bash
git add backend/requirements.txt backend/app/celery_app.py backend/app/tasks/__init__.py
git commit -m "feat(billing): Celery app setup with Beat schedule"
```

---

### Task 2: Billing Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/billing.py`

- [ ] **Step 1: Create billing schemas**

Create `backend/app/schemas/billing.py`:

```python
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.invoice import InvoiceStatus
from app.models.payment import PaymentMethod


# --- Invoice schemas ---

class InvoiceResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    plan_id: uuid.UUID
    amount: Decimal
    due_date: date
    status: InvoiceStatus
    paid_at: datetime | None
    issued_at: datetime
    created_at: datetime
    customer_name: str | None = None
    plan_name: str | None = None
    total_paid: Decimal | None = None

    model_config = {"from_attributes": True}


class InvoiceListResponse(BaseModel):
    items: list[InvoiceResponse]
    total: int
    page: int
    page_size: int


class InvoiceGenerateRequest(BaseModel):
    customer_id: uuid.UUID | None = None


class InvoiceUpdateRequest(BaseModel):
    status: InvoiceStatus | None = None
    amount: Decimal | None = None


# --- Payment schemas ---

class PaymentCreate(BaseModel):
    invoice_id: uuid.UUID
    amount: Decimal
    method: PaymentMethod
    reference_number: str | None = None


class PaymentResponse(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    amount: Decimal
    method: PaymentMethod
    reference_number: str | None
    received_by: uuid.UUID | None
    received_at: datetime
    created_at: datetime
    customer_name: str | None = None
    invoice_amount: Decimal | None = None

    model_config = {"from_attributes": True}


class PaymentListResponse(BaseModel):
    items: list[PaymentResponse]
    total: int
    page: int
    page_size: int


# --- Report schemas ---

class RevenueSummary(BaseModel):
    total_billed: Decimal
    total_collected: Decimal
    total_outstanding: Decimal
    collection_rate: float
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/schemas/billing.py
git commit -m "feat(billing): add billing Pydantic schemas"
```

---

### Task 3: Billing Service — Invoice Generation

**Files:**
- Create: `backend/app/services/billing.py`
- Create: `backend/tests/test_billing.py`

- [ ] **Step 1: Write tests for invoice generation**

Create `backend/tests/test_billing.py`:

```python
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.customer import Customer, CustomerStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.plan import Plan

API = settings.API_V1_PREFIX


@pytest_asyncio.fixture
async def plan(db_session: AsyncSession) -> Plan:
    p = Plan(
        id=uuid.uuid4(),
        name="Basic 10Mbps",
        download_mbps=10,
        upload_mbps=5,
        monthly_price=Decimal("999.00"),
        is_active=True,
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    return p


@pytest_asyncio.fixture
async def customer(db_session: AsyncSession, plan: Plan) -> Customer:
    c = Customer(
        id=uuid.uuid4(),
        full_name="Juan Dela Cruz",
        email="juan@test.com",
        phone="09171234567",
        pppoe_username="juan",
        pppoe_password="pass123",
        status=CustomerStatus.active,
        plan_id=plan.id,
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c


@pytest.mark.asyncio
async def test_generate_invoice(db_session: AsyncSession, customer: Customer, plan: Plan):
    from app.services.billing import generate_invoice

    billing_period = date(2026, 4, 1)
    invoice = await generate_invoice(db_session, customer, billing_period)

    assert invoice.customer_id == customer.id
    assert invoice.plan_id == plan.id
    assert invoice.amount == Decimal("999.00")
    assert invoice.due_date == date(2026, 4, settings.BILLING_DUE_DAY)
    assert invoice.status == InvoiceStatus.pending


@pytest.mark.asyncio
async def test_generate_invoice_idempotent(db_session: AsyncSession, customer: Customer, plan: Plan):
    from app.services.billing import generate_invoice

    billing_period = date(2026, 4, 1)
    inv1 = await generate_invoice(db_session, customer, billing_period)
    inv2 = await generate_invoice(db_session, customer, billing_period)

    assert inv1.id == inv2.id

    result = await db_session.execute(select(Invoice))
    assert len(result.scalars().all()) == 1


@pytest.mark.asyncio
async def test_generate_monthly_invoices(db_session: AsyncSession, customer: Customer):
    from app.services.billing import generate_monthly_invoices

    result = await generate_monthly_invoices(db_session)

    assert result["generated"] == 1
    assert result["skipped"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_billing.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.billing'`

- [ ] **Step 3: Implement billing service — invoice generation**

Create `backend/app/services/billing.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_billing.py -v`
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/billing.py backend/tests/test_billing.py
git commit -m "feat(billing): invoice generation service with tests"
```

---

### Task 4: Billing Service — Payment Recording + Auto-Reconnect

**Files:**
- Modify: `backend/app/services/billing.py`
- Modify: `backend/tests/test_billing.py`

- [ ] **Step 1: Write tests for payment recording**

Append to `backend/tests/test_billing.py`:

```python
from app.models.payment import Payment, PaymentMethod
from app.models.disconnect_log import DisconnectLog


@pytest_asyncio.fixture
async def invoice(db_session: AsyncSession, customer: Customer, plan: Plan) -> Invoice:
    inv = Invoice(
        id=uuid.uuid4(),
        customer_id=customer.id,
        plan_id=plan.id,
        amount=Decimal("999.00"),
        due_date=date(2026, 4, 15),
        status=InvoiceStatus.pending,
        issued_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
    )
    db_session.add(inv)
    await db_session.commit()
    await db_session.refresh(inv)
    return inv


@pytest.mark.asyncio
async def test_record_payment_full(db_session: AsyncSession, invoice: Invoice):
    from app.services.billing import record_payment

    payment = await record_payment(
        db=db_session,
        invoice_id=invoice.id,
        amount=Decimal("999.00"),
        method=PaymentMethod.cash,
        reference=None,
        received_by=None,
    )

    assert payment.amount == Decimal("999.00")
    await db_session.refresh(invoice)
    assert invoice.status == InvoiceStatus.paid
    assert invoice.paid_at is not None


@pytest.mark.asyncio
async def test_record_payment_partial(db_session: AsyncSession, invoice: Invoice):
    from app.services.billing import record_payment

    await record_payment(
        db=db_session,
        invoice_id=invoice.id,
        amount=Decimal("500.00"),
        method=PaymentMethod.cash,
        reference=None,
        received_by=None,
    )

    await db_session.refresh(invoice)
    assert invoice.status == InvoiceStatus.pending  # not fully paid


@pytest.mark.asyncio
async def test_auto_reconnect_on_full_payment(db_session: AsyncSession, customer: Customer, plan: Plan):
    from app.services.billing import record_payment

    # Make customer disconnected with an overdue invoice
    customer.status = CustomerStatus.disconnected
    inv = Invoice(
        id=uuid.uuid4(),
        customer_id=customer.id,
        plan_id=plan.id,
        amount=Decimal("999.00"),
        due_date=date(2026, 3, 15),
        status=InvoiceStatus.overdue,
        issued_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )
    db_session.add(inv)
    await db_session.commit()

    payment = await record_payment(
        db=db_session,
        invoice_id=inv.id,
        amount=Decimal("999.00"),
        method=PaymentMethod.bank,
        reference="REF123",
        received_by=None,
        skip_gateway=True,
    )

    await db_session.refresh(customer)
    assert customer.status == CustomerStatus.active

    result = await db_session.execute(select(DisconnectLog))
    log = result.scalar_one()
    assert log.action.value == "reconnect"
    assert log.reason.value == "non_payment"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_billing.py::test_record_payment_full -v`
Expected: FAIL with `ImportError: cannot import name 'record_payment'`

- [ ] **Step 3: Implement record_payment in billing service**

Append to `backend/app/services/billing.py`:

```python
async def record_payment(
    db: AsyncSession,
    invoice_id,
    amount: Decimal,
    method,
    reference: str | None,
    received_by=None,
    skip_gateway: bool = False,
) -> Payment:
    """Record a payment against an invoice. Auto-reconnects if fully paid and customer was suspended/disconnected."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise ValueError(f"Invoice {invoice_id} not found")

    payment = Payment(
        invoice_id=invoice.id,
        amount=amount,
        method=method,
        reference_number=reference,
        received_by=received_by,
        received_at=datetime.now(timezone.utc),
    )
    db.add(payment)
    await db.flush()

    # Check if invoice is fully paid
    pay_result = await db.execute(
        select(func.sum(Payment.amount)).where(Payment.invoice_id == invoice.id)
    )
    total_paid = pay_result.scalar() or Decimal("0")

    if total_paid >= invoice.amount:
        invoice.status = InvoiceStatus.paid
        invoice.paid_at = datetime.now(timezone.utc)

        # Auto-reconnect if customer was suspended/disconnected and no other overdue invoices
        customer = invoice.customer
        if customer.status in (CustomerStatus.suspended, CustomerStatus.disconnected):
            other_overdue = await db.execute(
                select(Invoice).where(
                    and_(
                        Invoice.customer_id == customer.id,
                        Invoice.id != invoice.id,
                        Invoice.status == InvoiceStatus.overdue,
                    )
                )
            )
            if not other_overdue.scalars().first():
                if not skip_gateway:
                    from app.services import gateway
                    try:
                        await gateway.reconnect_customer(str(customer.id), customer.pppoe_username)
                    except Exception as e:
                        logger.error(f"Gateway reconnect failed for {customer.id}: {e}")

                customer.status = CustomerStatus.active
                log = DisconnectLog(
                    customer_id=customer.id,
                    action=DisconnectAction.reconnect,
                    reason=DisconnectReason.non_payment,
                    performed_by=None,
                    performed_at=datetime.now(timezone.utc),
                )
                db.add(log)

    await db.flush()
    await db.refresh(payment)
    return payment
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_billing.py -v`
Expected: 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/billing.py backend/tests/test_billing.py
git commit -m "feat(billing): payment recording with auto-reconnect"
```

---

### Task 5: Billing Service — Overdue Check + Graduated Disconnect

**Files:**
- Modify: `backend/app/services/billing.py`
- Modify: `backend/tests/test_billing.py`

- [ ] **Step 1: Write tests for overdue check and graduated disconnect**

Append to `backend/tests/test_billing.py`:

```python
from datetime import timedelta


@pytest.mark.asyncio
async def test_check_overdue_invoices(db_session: AsyncSession, customer: Customer, plan: Plan):
    from app.services.billing import check_overdue_invoices

    # Past-due invoice
    inv = Invoice(
        id=uuid.uuid4(),
        customer_id=customer.id,
        plan_id=plan.id,
        amount=Decimal("999.00"),
        due_date=date.today() - timedelta(days=1),
        status=InvoiceStatus.pending,
        issued_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )
    db_session.add(inv)
    await db_session.commit()

    count = await check_overdue_invoices(db_session)
    assert count == 1

    await db_session.refresh(inv)
    assert inv.status == InvoiceStatus.overdue


@pytest.mark.asyncio
async def test_graduated_disconnect_throttle(db_session: AsyncSession, customer: Customer, plan: Plan):
    from app.services.billing import process_graduated_disconnect

    # Invoice overdue by enough days to trigger throttle
    days = settings.BILLING_THROTTLE_DAYS_AFTER_DUE
    inv = Invoice(
        id=uuid.uuid4(),
        customer_id=customer.id,
        plan_id=plan.id,
        amount=Decimal("999.00"),
        due_date=date.today() - timedelta(days=days),
        status=InvoiceStatus.overdue,
        issued_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )
    db_session.add(inv)
    await db_session.commit()

    result = await process_graduated_disconnect(db_session, skip_gateway=True)
    assert result["throttled"] == 1

    await db_session.refresh(customer)
    assert customer.status == CustomerStatus.suspended


@pytest.mark.asyncio
async def test_graduated_disconnect_disconnect(db_session: AsyncSession, customer: Customer, plan: Plan):
    from app.services.billing import process_graduated_disconnect

    # Already suspended, invoice overdue enough for disconnect
    customer.status = CustomerStatus.suspended
    days = settings.BILLING_DISCONNECT_DAYS_AFTER_DUE
    inv = Invoice(
        id=uuid.uuid4(),
        customer_id=customer.id,
        plan_id=plan.id,
        amount=Decimal("999.00"),
        due_date=date.today() - timedelta(days=days),
        status=InvoiceStatus.overdue,
        issued_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )
    db_session.add(inv)
    await db_session.commit()

    result = await process_graduated_disconnect(db_session, skip_gateway=True)
    assert result["disconnected"] == 1

    await db_session.refresh(customer)
    assert customer.status == CustomerStatus.disconnected


@pytest.mark.asyncio
async def test_graduated_disconnect_idempotent(db_session: AsyncSession, customer: Customer, plan: Plan):
    from app.services.billing import process_graduated_disconnect

    # Already disconnected — should not re-act
    customer.status = CustomerStatus.disconnected
    days = settings.BILLING_DISCONNECT_DAYS_AFTER_DUE
    inv = Invoice(
        id=uuid.uuid4(),
        customer_id=customer.id,
        plan_id=plan.id,
        amount=Decimal("999.00"),
        due_date=date.today() - timedelta(days=days),
        status=InvoiceStatus.overdue,
        issued_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )
    db_session.add(inv)
    await db_session.commit()

    result = await process_graduated_disconnect(db_session, skip_gateway=True)
    assert result["throttled"] == 0
    assert result["disconnected"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_billing.py::test_check_overdue_invoices -v`
Expected: FAIL

- [ ] **Step 3: Implement check_overdue_invoices and process_graduated_disconnect**

Append to `backend/app/services/billing.py`:

```python
async def check_overdue_invoices(db: AsyncSession) -> int:
    """Mark pending invoices past due date as overdue."""
    today = date.today()
    result = await db.execute(
        select(Invoice).where(
            and_(
                Invoice.status == InvoiceStatus.pending,
                Invoice.due_date < today,
            )
        )
    )
    invoices = result.scalars().all()
    for inv in invoices:
        inv.status = InvoiceStatus.overdue
    await db.flush()
    return len(invoices)


async def process_graduated_disconnect(db: AsyncSession, skip_gateway: bool = False) -> dict:
    """Apply graduated disconnect enforcement on overdue invoices."""
    today = date.today()
    result = await db.execute(
        select(Invoice).where(Invoice.status == InvoiceStatus.overdue)
    )
    invoices = result.scalars().all()

    throttled = 0
    disconnected = 0
    flagged = 0
    errors = []

    for inv in invoices:
        customer = inv.customer
        days_overdue = (today - inv.due_date).days

        try:
            # Throttle: customer is active and overdue enough
            if (
                days_overdue >= settings.BILLING_THROTTLE_DAYS_AFTER_DUE
                and customer.status == CustomerStatus.active
            ):
                if not skip_gateway:
                    from app.services import gateway
                    try:
                        await gateway.throttle_customer(
                            str(customer.id),
                            customer.pppoe_username,
                            settings.THROTTLE_DOWNLOAD_MBPS,
                            settings.THROTTLE_UPLOAD_KBPS,
                        )
                    except Exception as e:
                        logger.error(f"Gateway throttle failed for {customer.id}: {e}")

                customer.status = CustomerStatus.suspended
                db.add(DisconnectLog(
                    customer_id=customer.id,
                    action=DisconnectAction.throttle,
                    reason=DisconnectReason.non_payment,
                    performed_by=None,
                    performed_at=datetime.now(timezone.utc),
                ))
                throttled += 1

            # Disconnect: customer is suspended and overdue enough
            elif (
                days_overdue >= settings.BILLING_DISCONNECT_DAYS_AFTER_DUE
                and customer.status == CustomerStatus.suspended
            ):
                if not skip_gateway:
                    from app.services import gateway
                    try:
                        await gateway.disconnect_customer(str(customer.id), customer.pppoe_username)
                    except Exception as e:
                        logger.error(f"Gateway disconnect failed for {customer.id}: {e}")

                customer.status = CustomerStatus.disconnected
                db.add(DisconnectLog(
                    customer_id=customer.id,
                    action=DisconnectAction.disconnect,
                    reason=DisconnectReason.non_payment,
                    performed_by=None,
                    performed_at=datetime.now(timezone.utc),
                ))
                disconnected += 1

            # Flag for termination
            elif days_overdue >= settings.BILLING_TERMINATE_DAYS_AFTER_DUE:
                flagged += 1

        except Exception as e:
            logger.error(f"Graduated disconnect failed for customer {customer.id}: {e}")
            errors.append({"customer_id": str(customer.id), "error": str(e)})

    await db.flush()
    return {"throttled": throttled, "disconnected": disconnected, "flagged": flagged, "errors": errors}


async def send_billing_reminders(db: AsyncSession) -> int:
    """Create notification records for invoices due in BILLING_REMINDER_DAYS_BEFORE_DUE days."""
    today = date.today()
    reminder_date = today + __import__("datetime").timedelta(days=settings.BILLING_REMINDER_DAYS_BEFORE_DUE)

    result = await db.execute(
        select(Invoice).where(
            and_(
                Invoice.status == InvoiceStatus.pending,
                Invoice.due_date == reminder_date,
            )
        )
    )
    invoices = result.scalars().all()

    for inv in invoices:
        customer = inv.customer
        notification = Notification(
            customer_id=customer.id,
            type=NotificationType.sms,
            subject="Payment Reminder",
            message=f"Hi {customer.full_name}, your bill of ₱{inv.amount} is due on {inv.due_date}. Please pay before the due date to avoid service interruption.",
            status=NotificationStatus.pending,
        )
        db.add(notification)

    await db.flush()
    return len(invoices)


async def get_revenue_summary(db: AsyncSession, start_date: date, end_date: date) -> dict:
    """Get revenue summary for a date range."""
    billed_result = await db.execute(
        select(func.coalesce(func.sum(Invoice.amount), 0)).where(
            and_(
                Invoice.issued_at >= datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc),
                Invoice.issued_at <= datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc),
                Invoice.status != InvoiceStatus.void,
            )
        )
    )
    total_billed = billed_result.scalar() or Decimal("0")

    collected_result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            and_(
                Payment.received_at >= datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc),
                Payment.received_at <= datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc),
            )
        )
    )
    total_collected = collected_result.scalar() or Decimal("0")

    total_outstanding = total_billed - total_collected
    collection_rate = float(total_collected / total_billed * 100) if total_billed > 0 else 0.0

    return {
        "total_billed": total_billed,
        "total_collected": total_collected,
        "total_outstanding": total_outstanding,
        "collection_rate": round(collection_rate, 1),
    }
```

- [ ] **Step 4: Run all billing tests**

Run: `cd backend && python -m pytest tests/test_billing.py -v`
Expected: 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/billing.py backend/tests/test_billing.py
git commit -m "feat(billing): overdue check, graduated disconnect, reminders, revenue summary"
```

---

### Task 6: Billing API Endpoints

**Files:**
- Create: `backend/app/api/admin/billing.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create billing API router**

Create `backend/app/api/admin/billing.py`:

```python
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment
from app.models.plan import Plan
from app.models.user import User, UserRole
from app.schemas.billing import (
    InvoiceGenerateRequest,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceUpdateRequest,
    PaymentCreate,
    PaymentListResponse,
    PaymentResponse,
    RevenueSummary,
)
from app.services import billing as billing_service

router = APIRouter(prefix="/billing", tags=["billing"])


def _invoice_to_response(inv: Invoice) -> dict:
    total_paid = sum(p.amount for p in inv.payments) if inv.payments else Decimal("0")
    return {
        "id": inv.id,
        "customer_id": inv.customer_id,
        "plan_id": inv.plan_id,
        "amount": inv.amount,
        "due_date": inv.due_date,
        "status": inv.status,
        "paid_at": inv.paid_at,
        "issued_at": inv.issued_at,
        "created_at": inv.created_at,
        "customer_name": inv.customer.full_name if inv.customer else None,
        "plan_name": inv.plan.name if inv.plan else None,
        "total_paid": total_paid,
    }


# --- Invoice endpoints ---

@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices(
    customer_id: uuid.UUID | None = Query(None),
    status_filter: InvoiceStatus | None = Query(None, alias="status"),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Invoice)
    count_query = select(func.count(Invoice.id))

    if customer_id:
        query = query.where(Invoice.customer_id == customer_id)
        count_query = count_query.where(Invoice.customer_id == customer_id)
    if status_filter:
        query = query.where(Invoice.status == status_filter)
        count_query = count_query.where(Invoice.status == status_filter)
    if from_date:
        query = query.where(Invoice.issued_at >= datetime.combine(from_date, datetime.min.time()).replace(tzinfo=timezone.utc))
        count_query = count_query.where(Invoice.issued_at >= datetime.combine(from_date, datetime.min.time()).replace(tzinfo=timezone.utc))
    if to_date:
        query = query.where(Invoice.issued_at <= datetime.combine(to_date, datetime.max.time()).replace(tzinfo=timezone.utc))
        count_query = count_query.where(Invoice.issued_at <= datetime.combine(to_date, datetime.max.time()).replace(tzinfo=timezone.utc))

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Invoice.issued_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    invoices = result.scalars().all()

    return InvoiceListResponse(
        items=[_invoice_to_response(inv) for inv in invoices],
        total=total,
        page=page,
        page_size=size,
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return _invoice_to_response(invoice)


@router.post("/invoices/generate", status_code=status.HTTP_200_OK)
async def generate_invoices(
    body: InvoiceGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.billing)),
):
    if body.customer_id:
        result = await db.execute(select(Customer).where(Customer.id == body.customer_id))
        customer = result.scalar_one_or_none()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        invoice = await billing_service.generate_invoice(db, customer, date.today().replace(day=1))
        return {"generated": 1, "skipped": 0, "invoices": [str(invoice.id)]}
    else:
        result = await billing_service.generate_monthly_invoices(db)
        return result


@router.put("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: uuid.UUID,
    body: InvoiceUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.billing)),
):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if body.status is not None:
        invoice.status = body.status
    if body.amount is not None:
        invoice.amount = body.amount

    await db.flush()
    await db.refresh(invoice)
    return _invoice_to_response(invoice)


# --- Payment endpoints ---

@router.get("/payments", response_model=PaymentListResponse)
async def list_payments(
    customer_id: uuid.UUID | None = Query(None),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Payment)
    count_query = select(func.count(Payment.id))

    if customer_id:
        query = query.join(Invoice).where(Invoice.customer_id == customer_id)
        count_query = count_query.join(Invoice).where(Invoice.customer_id == customer_id)
    if from_date:
        query = query.where(Payment.received_at >= datetime.combine(from_date, datetime.min.time()).replace(tzinfo=timezone.utc))
        count_query = count_query.where(Payment.received_at >= datetime.combine(from_date, datetime.min.time()).replace(tzinfo=timezone.utc))
    if to_date:
        query = query.where(Payment.received_at <= datetime.combine(to_date, datetime.max.time()).replace(tzinfo=timezone.utc))
        count_query = count_query.where(Payment.received_at <= datetime.combine(to_date, datetime.max.time()).replace(tzinfo=timezone.utc))

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Payment.received_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    payments = result.scalars().all()

    items = []
    for p in payments:
        items.append({
            "id": p.id,
            "invoice_id": p.invoice_id,
            "amount": p.amount,
            "method": p.method,
            "reference_number": p.reference_number,
            "received_by": p.received_by,
            "received_at": p.received_at,
            "created_at": p.created_at,
            "customer_name": p.invoice.customer.full_name if p.invoice and p.invoice.customer else None,
            "invoice_amount": p.invoice.amount if p.invoice else None,
        })

    return PaymentListResponse(items=items, total=total, page=page, page_size=size)


@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    body: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.billing)),
):
    try:
        payment = await billing_service.record_payment(
            db=db,
            invoice_id=body.invoice_id,
            amount=body.amount,
            method=body.method,
            reference=body.reference_number,
            received_by=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    inv = payment.invoice
    return {
        "id": payment.id,
        "invoice_id": payment.invoice_id,
        "amount": payment.amount,
        "method": payment.method,
        "reference_number": payment.reference_number,
        "received_by": payment.received_by,
        "received_at": payment.received_at,
        "created_at": payment.created_at,
        "customer_name": inv.customer.full_name if inv and inv.customer else None,
        "invoice_amount": inv.amount if inv else None,
    }


# --- Report endpoint ---

@router.get("/reports/summary", response_model=RevenueSummary)
async def revenue_summary(
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.billing)),
):
    return await billing_service.get_revenue_summary(db, from_date, to_date)
```

- [ ] **Step 2: Register billing router in main.py**

In `backend/app/main.py`, add after the pppoe import:

```python
from app.api.admin.billing import router as billing_router
```

And add after the pppoe router inclusion:

```python
app.include_router(billing_router, prefix=settings.API_V1_PREFIX)
```

- [ ] **Step 3: Run all tests**

Run: `cd backend && python -m pytest -v`
Expected: All existing + billing tests PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/admin/billing.py backend/app/main.py
git commit -m "feat(billing): REST API endpoints for invoices, payments, reports"
```

---

### Task 7: Billing API Integration Tests

**Files:**
- Modify: `backend/tests/test_billing.py`

- [ ] **Step 1: Add API-level tests**

Append to `backend/tests/test_billing.py`:

```python
# --- API integration tests ---

@pytest_asyncio.fixture
async def plan_and_customer(client, auth_headers):
    """Create a plan and customer via API, return their IDs."""
    plan_resp = await client.post(
        f"{API}/plans/",
        json={"name": "Test Plan", "download_mbps": 10, "upload_mbps": 5, "monthly_price": "999.00"},
        headers=auth_headers,
    )
    plan_id = plan_resp.json()["id"]

    cust_resp = await client.post(
        f"{API}/customers/",
        json={
            "full_name": "API Test User",
            "email": "apitest@test.com",
            "phone": "09170000000",
            "pppoe_username": "apitest",
            "pppoe_password": "pass123",
            "plan_id": plan_id,
        },
        headers=auth_headers,
    )
    return plan_id, cust_resp.json()["id"]


@pytest.mark.asyncio
async def test_api_generate_invoices(client, auth_headers, plan_and_customer):
    plan_id, customer_id = plan_and_customer

    response = await client.post(
        f"{API}/billing/invoices/generate",
        json={"customer_id": customer_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["generated"] == 1


@pytest.mark.asyncio
async def test_api_list_invoices(client, auth_headers, plan_and_customer):
    plan_id, customer_id = plan_and_customer

    await client.post(
        f"{API}/billing/invoices/generate",
        json={"customer_id": customer_id},
        headers=auth_headers,
    )

    response = await client.get(f"{API}/billing/invoices", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_api_record_payment(client, auth_headers, plan_and_customer):
    plan_id, customer_id = plan_and_customer

    gen_resp = await client.post(
        f"{API}/billing/invoices/generate",
        json={"customer_id": customer_id},
        headers=auth_headers,
    )
    # Get the invoice
    inv_resp = await client.get(
        f"{API}/billing/invoices",
        params={"customer_id": customer_id},
        headers=auth_headers,
    )
    invoice_id = inv_resp.json()["items"][0]["id"]

    pay_resp = await client.post(
        f"{API}/billing/payments",
        json={
            "invoice_id": invoice_id,
            "amount": "999.00",
            "method": "cash",
        },
        headers=auth_headers,
    )
    assert pay_resp.status_code == 201
    assert pay_resp.json()["amount"] == "999.00"

    # Invoice should be paid now
    inv_detail = await client.get(f"{API}/billing/invoices/{invoice_id}", headers=auth_headers)
    assert inv_detail.json()["status"] == "paid"


@pytest.mark.asyncio
async def test_api_void_invoice(client, auth_headers, plan_and_customer):
    plan_id, customer_id = plan_and_customer

    await client.post(
        f"{API}/billing/invoices/generate",
        json={"customer_id": customer_id},
        headers=auth_headers,
    )
    inv_resp = await client.get(
        f"{API}/billing/invoices",
        params={"customer_id": customer_id},
        headers=auth_headers,
    )
    invoice_id = inv_resp.json()["items"][0]["id"]

    void_resp = await client.put(
        f"{API}/billing/invoices/{invoice_id}",
        json={"status": "void"},
        headers=auth_headers,
    )
    assert void_resp.status_code == 200
    assert void_resp.json()["status"] == "void"
```

- [ ] **Step 2: Run all tests**

Run: `cd backend && python -m pytest tests/test_billing.py -v`
Expected: 14 tests PASS

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_billing.py
git commit -m "test(billing): add API integration tests"
```

---

### Task 8: Celery Tasks

**Files:**
- Create: `backend/app/tasks/billing.py`

- [ ] **Step 1: Create Celery billing tasks**

Create `backend/app/tasks/billing.py`:

```python
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.celery_app import celery
from app.core.config import settings

logger = logging.getLogger(__name__)

SYNC_DATABASE_URL = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
sync_engine = create_engine(SYNC_DATABASE_URL, echo=False)


def _get_sync_session() -> Session:
    return Session(sync_engine)


@celery.task(name="app.tasks.billing.generate_monthly_invoices_task")
def generate_monthly_invoices_task():
    """Generate monthly invoices for all active customers. Runs on 1st of month."""
    import asyncio
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

    return asyncio.get_event_loop().run_until_complete(_run()) if _has_loop() else asyncio.run(_run())


@celery.task(name="app.tasks.billing.check_overdue_invoices_task")
def check_overdue_invoices_task():
    """Check for overdue invoices and mark them. Runs daily."""
    import asyncio
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

    return asyncio.get_event_loop().run_until_complete(_run()) if _has_loop() else asyncio.run(_run())


@celery.task(name="app.tasks.billing.process_graduated_disconnect_task")
def process_graduated_disconnect_task():
    """Process graduated disconnect enforcement. Runs daily."""
    import asyncio
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

    return asyncio.get_event_loop().run_until_complete(_run()) if _has_loop() else asyncio.run(_run())


@celery.task(name="app.tasks.billing.send_billing_reminders_task")
def send_billing_reminders_task():
    """Send billing reminders. Runs daily."""
    import asyncio
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

    return asyncio.get_event_loop().run_until_complete(_run()) if _has_loop() else asyncio.run(_run())


def _has_loop() -> bool:
    """Check if there's already a running event loop."""
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/tasks/billing.py
git commit -m "feat(billing): Celery tasks for scheduled billing operations"
```

---

### Task 9: Docker Compose — Add Celery Worker + Beat

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 1: Add celery-worker and celery-beat services**

In `docker-compose.yml`, add these services after the `frontend` service (before `volumes:`):

```yaml
  celery-worker:
    build:
      context: ./backend
    command: celery -A app.celery_app worker --loglevel=info --concurrency=2
    volumes:
      - ./backend:/app
    depends_on:
      - db
      - redis
    extra_hosts:
      - "gateway:192.168.40.41"
    environment:
      DATABASE_URL: postgresql+asyncpg://netbill:netbill@db:5432/netbill
      REDIS_URL: redis://redis:6379/0

  celery-beat:
    build:
      context: ./backend
    command: celery -A app.celery_app beat --loglevel=info -s /tmp/celerybeat-schedule
    volumes:
      - ./backend:/app
    depends_on:
      - db
      - redis
    environment:
      DATABASE_URL: postgresql+asyncpg://netbill:netbill@db:5432/netbill
      REDIS_URL: redis://redis:6379/0
```

- [ ] **Step 2: Commit**

```bash
git add docker-compose.yml
git commit -m "feat(billing): add Celery worker + Beat to Docker Compose"
```

---

### Task 10: Frontend — Billing API Client

**Files:**
- Create: `frontend/src/api/billing.ts`

- [ ] **Step 1: Create billing API client module**

Create `frontend/src/api/billing.ts`:

```typescript
import client from './client';

export interface Invoice {
  id: string;
  customer_id: string;
  plan_id: string;
  amount: string;
  due_date: string;
  status: string;
  paid_at: string | null;
  issued_at: string;
  created_at: string;
  customer_name: string | null;
  plan_name: string | null;
  total_paid: string | null;
}

export interface InvoiceListResponse {
  items: Invoice[];
  total: number;
  page: number;
  page_size: number;
}

export interface Payment {
  id: string;
  invoice_id: string;
  amount: string;
  method: string;
  reference_number: string | null;
  received_by: string | null;
  received_at: string;
  created_at: string;
  customer_name: string | null;
  invoice_amount: string | null;
}

export interface PaymentListResponse {
  items: Payment[];
  total: number;
  page: number;
  page_size: number;
}

export interface RevenueSummary {
  total_billed: string;
  total_collected: string;
  total_outstanding: string;
  collection_rate: number;
}

export const getInvoices = (params: {
  page?: number;
  size?: number;
  customer_id?: string;
  status?: string;
  from_date?: string;
  to_date?: string;
}) => client.get<InvoiceListResponse>('/billing/invoices', { params });

export const getInvoice = (id: string) => client.get<Invoice>(`/billing/invoices/${id}`);

export const generateInvoices = (customerId?: string) =>
  client.post('/billing/invoices/generate', { customer_id: customerId || null });

export const updateInvoice = (id: string, data: { status?: string; amount?: string }) =>
  client.put(`/billing/invoices/${id}`, data);

export const getPayments = (params: {
  page?: number;
  size?: number;
  customer_id?: string;
  from_date?: string;
  to_date?: string;
}) => client.get<PaymentListResponse>('/billing/payments', { params });

export const recordPayment = (data: {
  invoice_id: string;
  amount: string;
  method: string;
  reference_number?: string;
}) => client.post<Payment>('/billing/payments', data);

export const getRevenueSummary = (params: { from_date: string; to_date: string }) =>
  client.get<RevenueSummary>('/billing/reports/summary', { params });
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/billing.ts
git commit -m "feat(billing): frontend API client module"
```

---

### Task 11: Frontend — Invoices Page

**Files:**
- Modify: `frontend/src/pages/billing/Invoices.tsx`

- [ ] **Step 1: Rewrite Invoices page with full API integration**

Replace entire contents of `frontend/src/pages/billing/Invoices.tsx`:

```tsx
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Table, Card, Typography, Select, Space, Button, message, Tag, DatePicker, Popconfirm } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import StatusTag from '../../components/StatusTag';
import { getInvoices, generateInvoices, updateInvoice } from '../../api/billing';
import type { Invoice } from '../../api/billing';

const Invoices = () => {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null] | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['invoices', page, statusFilter, dateRange],
    queryFn: () =>
      getInvoices({
        page,
        size: 20,
        status: statusFilter,
        from_date: dateRange?.[0]?.format('YYYY-MM-DD'),
        to_date: dateRange?.[1]?.format('YYYY-MM-DD'),
      }).then((r) => r.data),
  });

  const generateMut = useMutation({
    mutationFn: () => generateInvoices(),
    onSuccess: (res) => {
      message.success(`Generated ${res.data.generated} invoice(s), skipped ${res.data.skipped}`);
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
    },
    onError: () => message.error('Failed to generate invoices'),
  });

  const voidMut = useMutation({
    mutationFn: (id: string) => updateInvoice(id, { status: 'void' }),
    onSuccess: () => {
      message.success('Invoice voided');
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
    },
    onError: () => message.error('Failed to void invoice'),
  });

  const columns = [
    {
      title: 'Customer',
      dataIndex: 'customer_name',
      key: 'customer',
      ellipsis: true,
    },
    {
      title: 'Amount',
      key: 'amount',
      render: (_: unknown, r: Invoice) => `₱${Number(r.amount).toLocaleString('en-PH', { minimumFractionDigits: 2 })}`,
      width: 120,
    },
    {
      title: 'Paid',
      key: 'total_paid',
      render: (_: unknown, r: Invoice) => r.total_paid ? `₱${Number(r.total_paid).toLocaleString('en-PH', { minimumFractionDigits: 2 })}` : '₱0.00',
      width: 120,
    },
    {
      title: 'Due Date',
      dataIndex: 'due_date',
      key: 'due',
      width: 110,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (s: string) => <StatusTag status={s} />,
      width: 100,
    },
    {
      title: 'Issued',
      dataIndex: 'issued_at',
      key: 'issued',
      render: (d: string) => dayjs(d).format('YYYY-MM-DD'),
      width: 110,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 80,
      render: (_: unknown, r: Invoice) =>
        r.status !== 'void' && r.status !== 'paid' ? (
          <Popconfirm title="Void this invoice?" onConfirm={() => voidMut.mutate(r.id)}>
            <Button type="link" size="small" danger>Void</Button>
          </Popconfirm>
        ) : null,
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>Invoices</Typography.Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          loading={generateMut.isPending}
          onClick={() => generateMut.mutate()}
        >
          Generate Invoices
        </Button>
      </div>
      <Card>
        <Space style={{ marginBottom: 16 }} wrap>
          <Select
            placeholder="Filter by status"
            allowClear
            style={{ width: 150 }}
            value={statusFilter}
            onChange={setStatusFilter}
          >
            <Select.Option value="pending">Pending</Select.Option>
            <Select.Option value="paid">Paid</Select.Option>
            <Select.Option value="overdue">Overdue</Select.Option>
            <Select.Option value="void">Void</Select.Option>
          </Select>
          <DatePicker.RangePicker
            onChange={(dates) => setDateRange(dates as [dayjs.Dayjs | null, dayjs.Dayjs | null] | null)}
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={() => queryClient.invalidateQueries({ queryKey: ['invoices'] })}
          />
        </Space>
        <Table
          columns={columns}
          dataSource={data?.items || []}
          rowKey="id"
          loading={isLoading}
          pagination={{
            current: page,
            pageSize: 20,
            total: data?.total || 0,
            onChange: setPage,
            showTotal: (total) => `${total} invoices`,
          }}
        />
      </Card>
    </div>
  );
};

export default Invoices;
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/billing/Invoices.tsx
git commit -m "feat(billing): wire Invoices page to API"
```

---

### Task 12: Frontend — Payments Page

**Files:**
- Modify: `frontend/src/pages/billing/Payments.tsx`

- [ ] **Step 1: Rewrite Payments page with full API integration**

Replace entire contents of `frontend/src/pages/billing/Payments.tsx`:

```tsx
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Table, Card, Typography, Button, Modal, Form, Input, Select, InputNumber, message, Space, DatePicker } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { getPayments, recordPayment } from '../../api/billing';
import { getInvoices } from '../../api/billing';
import type { Payment, Invoice } from '../../api/billing';

const Payments = () => {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null] | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['payments', page, dateRange],
    queryFn: () =>
      getPayments({
        page,
        size: 20,
        from_date: dateRange?.[0]?.format('YYYY-MM-DD'),
        to_date: dateRange?.[1]?.format('YYYY-MM-DD'),
      }).then((r) => r.data),
  });

  // Fetch unpaid invoices for the payment modal
  const { data: unpaidInvoices } = useQuery({
    queryKey: ['invoices-unpaid'],
    queryFn: () =>
      getInvoices({ size: 100, status: 'pending' })
        .then((r) => r.data.items)
        .then(async (pending) => {
          const overdueResp = await getInvoices({ size: 100, status: 'overdue' });
          return [...pending, ...overdueResp.data.items];
        }),
    enabled: modalOpen,
  });

  const payMut = useMutation({
    mutationFn: recordPayment,
    onSuccess: () => {
      message.success('Payment recorded');
      setModalOpen(false);
      form.resetFields();
      setSelectedInvoice(null);
      queryClient.invalidateQueries({ queryKey: ['payments'] });
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
    },
    onError: () => message.error('Failed to record payment'),
  });

  const columns = [
    {
      title: 'Customer',
      dataIndex: 'customer_name',
      key: 'customer',
      ellipsis: true,
    },
    {
      title: 'Amount',
      key: 'amount',
      render: (_: unknown, r: Payment) => `₱${Number(r.amount).toLocaleString('en-PH', { minimumFractionDigits: 2 })}`,
      width: 120,
    },
    {
      title: 'Method',
      dataIndex: 'method',
      key: 'method',
      render: (m: string) => m.charAt(0).toUpperCase() + m.slice(1),
      width: 90,
    },
    {
      title: 'Reference',
      dataIndex: 'reference_number',
      key: 'ref',
      render: (r: string | null) => r || '-',
      width: 140,
    },
    {
      title: 'Invoice Amount',
      key: 'invoice_amount',
      render: (_: unknown, r: Payment) => r.invoice_amount ? `₱${Number(r.invoice_amount).toLocaleString('en-PH', { minimumFractionDigits: 2 })}` : '-',
      width: 130,
    },
    {
      title: 'Date',
      dataIndex: 'received_at',
      key: 'date',
      render: (d: string) => dayjs(d).format('YYYY-MM-DD HH:mm'),
      width: 150,
    },
  ];

  const handleInvoiceSelect = (invoiceId: string) => {
    const inv = unpaidInvoices?.find((i) => i.id === invoiceId) || null;
    setSelectedInvoice(inv);
    if (inv) {
      const paid = Number(inv.total_paid || 0);
      const remaining = Number(inv.amount) - paid;
      form.setFieldsValue({ amount: remaining > 0 ? remaining : Number(inv.amount) });
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>Payments</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          Record Payment
        </Button>
      </div>
      <Card>
        <Space style={{ marginBottom: 16 }} wrap>
          <DatePicker.RangePicker
            onChange={(dates) => setDateRange(dates as [dayjs.Dayjs | null, dayjs.Dayjs | null] | null)}
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={() => queryClient.invalidateQueries({ queryKey: ['payments'] })}
          />
        </Space>
        <Table
          columns={columns}
          dataSource={data?.items || []}
          rowKey="id"
          loading={isLoading}
          pagination={{
            current: page,
            pageSize: 20,
            total: data?.total || 0,
            onChange: setPage,
            showTotal: (total) => `${total} payments`,
          }}
        />
      </Card>

      <Modal
        title="Record Payment"
        open={modalOpen}
        onCancel={() => { setModalOpen(false); form.resetFields(); setSelectedInvoice(null); }}
        onOk={() => form.submit()}
        confirmLoading={payMut.isPending}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) =>
            payMut.mutate({
              invoice_id: values.invoice_id,
              amount: String(values.amount),
              method: values.method,
              reference_number: values.reference_number || undefined,
            })
          }
        >
          <Form.Item name="invoice_id" label="Invoice" rules={[{ required: true, message: 'Select an invoice' }]}>
            <Select
              showSearch
              placeholder="Search by customer name"
              optionFilterProp="label"
              onChange={handleInvoiceSelect}
              options={(unpaidInvoices || []).map((inv) => ({
                value: inv.id,
                label: `${inv.customer_name} - ₱${Number(inv.amount).toFixed(2)} (due ${inv.due_date})`,
              }))}
            />
          </Form.Item>
          {selectedInvoice && (
            <div style={{ marginBottom: 16, padding: 8, background: '#f5f5f5', borderRadius: 4, fontSize: 13 }}>
              Invoice: ₱{Number(selectedInvoice.amount).toFixed(2)} | Paid: ₱{Number(selectedInvoice.total_paid || 0).toFixed(2)} | Remaining: ₱{(Number(selectedInvoice.amount) - Number(selectedInvoice.total_paid || 0)).toFixed(2)}
            </div>
          )}
          <Form.Item name="amount" label="Amount" rules={[{ required: true, message: 'Enter amount' }]}>
            <InputNumber style={{ width: '100%' }} min={0.01} precision={2} prefix="₱" />
          </Form.Item>
          <Form.Item name="method" label="Payment Method" rules={[{ required: true, message: 'Select method' }]}>
            <Select>
              <Select.Option value="cash">Cash</Select.Option>
              <Select.Option value="bank">Bank Transfer</Select.Option>
              <Select.Option value="online">Online</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="reference_number" label="Reference Number">
            <Input placeholder="Bank ref, receipt #, etc." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Payments;
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/billing/Payments.tsx
git commit -m "feat(billing): wire Payments page with Record Payment modal"
```

---

### Task 13: Deploy + Smoke Test

**Files:** None (deployment only)

- [ ] **Step 1: SSH to App Server and pull latest code**

```bash
ssh root@192.168.40.40 "cd /root/2maXnetBill && git pull"
```

- [ ] **Step 2: Rebuild and restart Docker containers**

```bash
ssh root@192.168.40.40 "cd /root/2maXnetBill && docker compose build && docker compose up -d"
```

- [ ] **Step 3: Run Alembic migration (if new columns needed)**

```bash
ssh root@192.168.40.40 "cd /root/2maXnetBill && docker compose exec backend alembic upgrade head"
```

- [ ] **Step 4: Verify Celery worker and Beat are running**

```bash
ssh root@192.168.40.40 "docker compose logs celery-worker --tail 20"
ssh root@192.168.40.40 "docker compose logs celery-beat --tail 20"
```

Expected: Worker shows "celery@... ready", Beat shows schedule loaded.

- [ ] **Step 5: Smoke test billing API via curl**

```bash
# Login
TOKEN=$(ssh root@192.168.40.40 "curl -s http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"admin\",\"password\":\"admin123\"}'" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Generate invoices
ssh root@192.168.40.40 "curl -s http://localhost:8000/api/v1/billing/invoices/generate -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json' -d '{}' -X POST"

# List invoices
ssh root@192.168.40.40 "curl -s http://localhost:8000/api/v1/billing/invoices -H 'Authorization: Bearer $TOKEN'"
```

- [ ] **Step 6: Verify frontend at http://192.168.40.40**

Open browser, navigate to Billing > Invoices and Billing > Payments. Confirm data loads and "Generate Invoices" + "Record Payment" work.

- [ ] **Step 7: Commit any deployment fixes if needed**
