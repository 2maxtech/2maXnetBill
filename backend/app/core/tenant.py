from fastapi import Depends, Header
from typing import Optional
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole

async def get_tenant_id(
    current_user: User = Depends(get_current_user),
    x_tenant_id: Optional[str] = Header(None),
) -> str:
    """Resolve effective tenant ID.

    - Regular admin: returns their own user ID
    - Super admin without header: returns their own ID
    - Super admin with X-Tenant-Id header: returns the impersonated tenant's ID
    """
    if current_user.role == UserRole.super_admin and x_tenant_id:
        return x_tenant_id
    return str(current_user.id)
