from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.kerio import kerio

router = APIRouter(prefix="/kerio", tags=["kerio"])


@router.get("/active-hosts")
async def get_active_hosts(current_user: User = Depends(get_current_user)):
    """Get currently connected hosts from Kerio Control."""
    try:
        await kerio.login()
        hosts = await kerio.get_active_hosts()
        return {"hosts": hosts, "total": len(hosts)}
    except Exception as e:
        return {"hosts": [], "total": 0, "error": str(e)}


@router.get("/status")
async def get_kerio_status(current_user: User = Depends(get_current_user)):
    """Check Kerio Control connectivity."""
    try:
        await kerio.login()
        interfaces = await kerio.get_interfaces()
        return {"connected": True, "interfaces": len(interfaces)}
    except Exception as e:
        return {"connected": False, "error": str(e)}


@router.get("/users")
async def get_kerio_users(current_user: User = Depends(get_current_user)):
    """Get local users from Kerio Control."""
    try:
        await kerio.login()
        users = await kerio.get_users()
        return {"users": users, "total": len(users)}
    except Exception as e:
        return {"users": [], "total": 0, "error": str(e)}
