import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.customer import Customer, CustomerStatus
from app.models.disconnect_log import DisconnectLog
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment, PaymentMethod
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
