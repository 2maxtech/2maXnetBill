import logging
import re
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.customer import Customer, CustomerStatus
from app.models.plan import Plan
from app.models.user import User
from app.services.mikrotik import mikrotik

logger = logging.getLogger(__name__)


def _parse_rate(rate_str: str) -> tuple[int, int]:
    """Parse MikroTik rate-limit 'upload/download' into (download_mbps, upload_mbps).
    Handles formats like '5M/10M', '512k/1M', '10000000/5000000'.
    """
    if not rate_str or "/" not in rate_str:
        return 0, 0

    upload_str, download_str = rate_str.split("/", 1)

    def to_mbps(s: str) -> int:
        s = s.strip().lower()
        if s.endswith("m"):
            return int(float(s[:-1]))
        elif s.endswith("k"):
            return max(1, int(float(s[:-1]) / 1000))
        else:
            return max(1, int(float(s)) // 1_000_000) if s.isdigit() else 0

    return to_mbps(download_str), to_mbps(upload_str)

router = APIRouter(prefix="/network", tags=["network"])


@router.get("/active-sessions")
async def get_active_sessions(current_user: User = Depends(get_current_user)):
    """Get active PPPoE sessions from MikroTik."""
    try:
        sessions = await mikrotik.get_active_sessions()
        return {"sessions": sessions, "total": len(sessions)}
    except Exception as e:
        return {"sessions": [], "total": 0, "error": str(e)}


@router.get("/status")
async def get_network_status(current_user: User = Depends(get_current_user)):
    """Check MikroTik connectivity."""
    try:
        identity = await mikrotik.get_identity()
        resources = await mikrotik.get_resources()
        return {
            "connected": True,
            "identity": identity,
            "uptime": resources.get("uptime", ""),
            "cpu_load": resources.get("cpu-load", ""),
            "free_memory": resources.get("free-memory", ""),
        }
    except Exception as e:
        return {"connected": False, "error": str(e)}


@router.get("/subscribers")
async def get_subscribers(current_user: User = Depends(get_current_user)):
    """List PPPoE secrets from MikroTik."""
    try:
        secrets = await mikrotik.get_secrets()
        return {"subscribers": secrets, "total": len(secrets)}
    except Exception as e:
        return {"subscribers": [], "total": 0, "error": str(e)}


@router.post("/import")
async def import_from_mikrotik(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Import existing PPPoE secrets and profiles from MikroTik into NetLedger.

    - Creates Plans from MikroTik profiles that have rate-limits
    - Creates Customers from PPPoE secrets not already in NetLedger
    - Skips secrets that match an existing customer's pppoe_username or mikrotik_secret_id
    """
    try:
        mt_profiles = await mikrotik.get_profiles()
        mt_secrets = await mikrotik.get_secrets()
    except Exception as e:
        return {"error": f"Failed to connect to MikroTik: {e}"}

    # Build profile → rate-limit map
    profile_rates: dict[str, str] = {}
    for p in mt_profiles:
        if p.get("rate-limit"):
            profile_rates[p["name"]] = p["rate-limit"]

    # Get existing customers to skip duplicates
    existing_result = await db.execute(select(Customer))
    existing_customers = existing_result.scalars().all()
    existing_usernames = {c.pppoe_username for c in existing_customers}
    existing_secret_ids = {c.mikrotik_secret_id for c in existing_customers if c.mikrotik_secret_id}

    # Get existing plans to avoid duplicates
    existing_plans_result = await db.execute(select(Plan))
    existing_plans = existing_plans_result.scalars().all()
    existing_plan_names = {p.name for p in existing_plans}

    # Create plans from profiles with rate-limits
    profile_to_plan: dict[str, Plan] = {}
    plans_created = 0

    for profile_name, rate_limit in profile_rates.items():
        download_mbps, upload_mbps = _parse_rate(rate_limit)
        if download_mbps == 0 and upload_mbps == 0:
            continue

        plan_name = f"{profile_name}"
        if plan_name in existing_plan_names:
            # Map to existing plan with same name
            plan = next((p for p in existing_plans if p.name == plan_name), None)
            if plan:
                profile_to_plan[profile_name] = plan
            continue

        plan = Plan(
            name=plan_name,
            download_mbps=download_mbps,
            upload_mbps=upload_mbps,
            monthly_price=Decimal("0.00"),  # Admin sets pricing later
            description=f"Imported from MikroTik profile '{profile_name}'",
            is_active=True,
        )
        db.add(plan)
        await db.flush()
        await db.refresh(plan)
        profile_to_plan[profile_name] = plan
        existing_plan_names.add(plan_name)
        plans_created += 1

    # Also map profiles without rate-limits to the default plan if one exists
    # Secrets on 'default' profile get no plan assignment (admin handles later)

    # Create customers from secrets
    customers_created = 0
    customers_skipped = 0

    for secret in mt_secrets:
        secret_id = secret.get(".id", "")
        username = secret.get("name", "")

        if not username:
            continue

        # Skip if already exists
        if username in existing_usernames or secret_id in existing_secret_ids:
            customers_skipped += 1
            continue

        profile_name = secret.get("profile", "default")
        plan = profile_to_plan.get(profile_name)

        # If no plan mapped, try matching by speed pattern in profile name
        if not plan and profile_name != "default":
            # Try to find existing plan with matching speeds
            download_mbps, upload_mbps = _parse_rate(profile_rates.get(profile_name, ""))
            for ep in existing_plans:
                if ep.download_mbps == download_mbps and ep.upload_mbps == upload_mbps:
                    plan = ep
                    break

        if not plan:
            # Use first active plan as fallback, or skip
            fallback = next((p for p in existing_plans if p.is_active), None)
            if not fallback and profile_to_plan:
                fallback = next(iter(profile_to_plan.values()))
            if not fallback:
                logger.warning(f"Skipping secret '{username}' — no plan available")
                customers_skipped += 1
                continue
            plan = fallback

        customer = Customer(
            full_name=username.replace(".", " ").replace("_", " ").title(),
            email=f"{username}@imported.local",
            phone="0000000000",
            pppoe_username=username,
            pppoe_password=secret.get("password", "imported"),
            status=CustomerStatus.disconnected if secret.get("disabled") == "true" else CustomerStatus.active,
            plan_id=plan.id,
            mikrotik_secret_id=secret_id,
            mac_address=secret.get("caller-id") or None,
        )
        db.add(customer)
        existing_usernames.add(username)
        customers_created += 1

    await db.flush()

    return {
        "plans_created": plans_created,
        "customers_created": customers_created,
        "customers_skipped": customers_skipped,
        "total_secrets_on_mikrotik": len(mt_secrets),
        "profiles_with_rates": len(profile_rates),
    }
