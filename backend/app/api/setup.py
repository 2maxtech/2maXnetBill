from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, hash_password
from app.models.router import Router
from app.models.user import User, UserRole
from app.schemas.setup import SetupRequest, SetupStatusResponse

router = APIRouter(prefix="/setup", tags=["setup"])


@router.get("/status", response_model=SetupStatusResponse)
async def setup_status(db: AsyncSession = Depends(get_db)):
    """Check if the app has been configured (public endpoint)."""
    result = await db.execute(select(func.count()).select_from(User).where(User.role == UserRole.admin))
    admin_count = result.scalar() or 0
    return SetupStatusResponse(
        configured=admin_count > 0,
        deployment_mode=settings.DEPLOYMENT_MODE,
    )


@router.post("/initialize")
async def initialize(body: SetupRequest, db: AsyncSession = Depends(get_db)):
    """First-time setup: create admin user and optionally first router."""
    if settings.DEPLOYMENT_MODE != "onpremise":
        raise HTTPException(status_code=404, detail="Not found")

    result = await db.execute(select(func.count()).select_from(User).where(User.role == UserRole.admin))
    if (result.scalar() or 0) > 0:
        raise HTTPException(status_code=403, detail="Application is already configured")

    from sqlalchemy import or_
    existing = await db.execute(
        select(User).where(or_(User.username == body.admin_username, User.email == body.admin_email))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username or email already exists")

    user = User(
        username=body.admin_username,
        email=body.admin_email,
        password_hash=hash_password(body.admin_password),
        full_name=body.company_name,
        company_name=body.company_name,
        role=UserRole.admin,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    router_created = False
    if body.router_name and body.router_url:
        url = body.router_url
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
        r = Router(
            name=body.router_name,
            url=url,
            username=body.router_username,
            password=body.router_password,
            owner_id=user.id,
        )
        db.add(r)
        await db.flush()
        router_created = True

    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token = create_refresh_token(str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user_id": str(user.id),
        "router_created": router_created,
        "message": "Setup complete! Welcome to NetLedger.",
    }
