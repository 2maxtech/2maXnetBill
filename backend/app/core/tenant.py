from fastapi import Depends, Header
from typing import Optional
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole

async def get_tenant_id(
    current_user: User = Depends(get_current_user),
    x_tenant_id: Optional[str] = Header(None),
) -> str:
    """Resolve effective tenant ID.
    On-premise: always returns current user's ID (single tenant).
    SaaS: regular admin=own ID, super admin with header=impersonated tenant.
    """
    if settings.DEPLOYMENT_MODE == "onpremise":
        return str(current_user.id)
    if current_user.role == UserRole.super_admin and x_tenant_id:
        return x_tenant_id
    return str(current_user.id)
