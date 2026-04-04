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
