"""NAT redirect management for overdue customer browser notification.

Creates/removes MikroTik firewall NAT dstnat rules to redirect overdue
customers' HTTP traffic to a payment notification page.
"""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.app_setting import AppSetting
from app.models.customer import Customer
from app.services.mikrotik import MikroTikClient, get_client_for_customer

logger = logging.getLogger(__name__)

COMMENT_PREFIX = "netledger-redirect-"


def _make_comment(customer_id: uuid.UUID) -> str:
    """Build the NAT rule comment for a customer."""
    return f"{COMMENT_PREFIX}{customer_id}"


async def _get_tenant_redirect_settings(db: AsyncSession, owner_id: uuid.UUID) -> dict:
    """Load NAT redirect settings for a tenant."""
    keys = ["nat_redirect_enabled", "nat_redirect_ip", "portal_slug"]
    result = await db.execute(
        select(AppSetting).where(
            AppSetting.key.in_(keys),
            AppSetting.owner_id == owner_id,
        )
    )
    return {s.key: s.value for s in result.scalars().all()}


async def add_redirect_for_customer(db: AsyncSession, customer: Customer) -> bool:
    """Add a NAT redirect rule for a throttled/overdue customer.

    Returns True if redirect was created, False if skipped or failed.
    """
    tenant_settings = await _get_tenant_redirect_settings(db, customer.owner_id)

    # Check if feature is enabled for this tenant
    if tenant_settings.get("nat_redirect_enabled") != "true":
        return False

    redirect_ip = tenant_settings.get("nat_redirect_ip", "")
    if not redirect_ip:
        logger.warning("NAT redirect enabled but no redirect IP for tenant %s", customer.owner_id)
        return False

    slug = tenant_settings.get("portal_slug", "")
    if not slug:
        logger.warning("NAT redirect: no portal_slug for tenant %s", customer.owner_id)
        return False

    try:
        client, _ = await get_client_for_customer(db, customer)
        if not client:
            logger.warning("NAT redirect: no MikroTik client for customer %s", customer.id)
            return False

        # Get customer's current PPPoE IP
        ip = await client.get_active_session_ip(customer.pppoe_username)
        if not ip:
            logger.info("NAT redirect: customer %s has no active session, skipping", customer.pppoe_username)
            return False

        comment = _make_comment(customer.id)

        # Remove any existing redirect first (idempotent)
        await client.remove_nat_redirect(comment)

        # Create new redirect rule
        await client.add_nat_redirect(
            src_address=ip,
            to_address=redirect_ip,
            to_port=80,
            comment=comment,
        )
        logger.info("NAT redirect added for %s (%s) → %s", customer.pppoe_username, ip, redirect_ip)
        return True

    except Exception as e:
        logger.error("NAT redirect failed for customer %s: %s", customer.id, e)
        return False


async def remove_redirect_for_customer(db: AsyncSession, customer: Customer) -> bool:
    """Remove NAT redirect rules for a customer.

    Returns True if any rules were removed, False otherwise.
    """
    try:
        client, _ = await get_client_for_customer(db, customer)
        if not client:
            return False

        comment = _make_comment(customer.id)
        removed = await client.remove_nat_redirect(comment)
        if removed > 0:
            logger.info("NAT redirect removed for %s (%d rules)", customer.pppoe_username, removed)
        return removed > 0

    except Exception as e:
        logger.error("NAT redirect removal failed for customer %s: %s", customer.id, e)
        return False


async def check_redirect_for_customer(db: AsyncSession, customer: Customer) -> dict | None:
    """Check if a NAT redirect rule exists for a customer.

    Returns the rule dict if found, None otherwise.
    """
    try:
        client, _ = await get_client_for_customer(db, customer)
        if not client:
            return None

        comment = _make_comment(customer.id)
        rules = await client.get_nat_redirects(comment)
        for rule in rules:
            if rule.get("comment") == comment:
                return {
                    "id": rule.get(".id"),
                    "src_address": rule.get("src-address"),
                    "to_address": rule.get("to-addresses"),
                    "to_port": rule.get("to-ports"),
                    "comment": rule.get("comment"),
                    "disabled": rule.get("disabled", "false"),
                }
        return None

    except Exception as e:
        logger.error("NAT redirect check failed for customer %s: %s", customer.id, e)
        return None
