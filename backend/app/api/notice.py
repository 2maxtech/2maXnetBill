"""Public overdue notice endpoints — no auth required.

GET  /notice/{slug}     — tenant branding + portal URL for the overdue notification page
POST /notice/lookup      — look up a customer's portal by PPPoE username
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.app_setting import AppSetting
from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notice", tags=["notice"])


async def _get_settings_by_slug(db: AsyncSession, slug: str) -> dict:
    """Look up tenant by portal_slug and return branding + portal URL."""
    result = await db.execute(
        select(AppSetting).where(
            AppSetting.key == "portal_slug",
            AppSetting.value == slug,
        )
    )
    slug_setting = result.scalar_one_or_none()
    if not slug_setting:
        return {}

    owner_id = slug_setting.owner_id

    # Load branding settings for this tenant
    keys = ["company_name", "company_logo_url", "primary_color"]
    settings_result = await db.execute(
        select(AppSetting).where(
            AppSetting.key.in_(keys),
            AppSetting.owner_id == owner_id,
        )
    )
    tenant_settings = {s.key: s.value for s in settings_result.scalars().all()}

    portal_url = f"{settings.BASE_URL}/portal/{slug}/login"

    return {
        "company_name": tenant_settings.get("company_name", "Your ISP"),
        "company_logo_url": tenant_settings.get("company_logo_url", ""),
        "primary_color": tenant_settings.get("primary_color", "#e8700a"),
        "portal_url": portal_url,
        "slug": slug,
    }


class LookupRequest(BaseModel):
    username: str


@router.post("/lookup")
async def lookup_portal(body: LookupRequest, db: AsyncSession = Depends(get_db)):
    """Look up a customer's ISP portal by PPPoE username.

    Used by the generic overdue page when the customer enters their username.
    """
    username = body.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    result = await db.execute(
        select(Customer).where(Customer.pppoe_username == username).limit(1)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Account not found. Please check your PPPoE username and try again.")

    # Find tenant's portal slug
    slug_result = await db.execute(
        select(AppSetting).where(
            AppSetting.key == "portal_slug",
            AppSetting.owner_id == customer.owner_id,
        )
    )
    slug_setting = slug_result.scalar_one_or_none()
    if not slug_setting or not slug_setting.value:
        raise HTTPException(status_code=404, detail="Portal not configured for your provider")

    slug = slug_setting.value
    data = await _get_settings_by_slug(db, slug)

    # Include unpaid invoices with payment links
    inv_result = await db.execute(
        select(Invoice).where(
            and_(
                Invoice.customer_id == customer.id,
                Invoice.status.in_([InvoiceStatus.pending, InvoiceStatus.overdue]),
            )
        ).order_by(Invoice.due_date.desc())
    )
    invoices = []
    for inv in inv_result.scalars().all():
        entry = {
            "amount": float(inv.amount),
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "status": inv.status.value,
        }
        if inv.payment_token:
            entry["payment_url"] = f"{settings.BASE_URL}/pay/{inv.payment_token}"
        invoices.append(entry)

    data["customer_name"] = customer.full_name
    data["invoices"] = invoices
    data["total_due"] = sum(i["amount"] for i in invoices)
    return data


@router.get("/{slug}")
async def get_overdue_notice(slug: str, db: AsyncSession = Depends(get_db)):
    """Return tenant branding and portal URL for the overdue notification page."""
    data = await _get_settings_by_slug(db, slug)
    if not data:
        raise HTTPException(status_code=404, detail="Provider not found")
    return data
