import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.support_ticket import SupportTicket, SupportTicketStatus
from app.models.user import User, UserRole

router = APIRouter(prefix="/support", tags=["support"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SupportTicketResponse(BaseModel):
    id: uuid.UUID
    subject: str
    description: str
    status: SupportTicketStatus
    category: str
    tenant_name: str | None
    tenant_email: str | None
    chat_history: str | None
    image_urls: str | None
    admin_notes: str | None
    owner_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SupportTicketUpdate(BaseModel):
    status: SupportTicketStatus | None = None
    admin_notes: str | None = None


class PaginatedTickets(BaseModel):
    items: list[SupportTicketResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Endpoints (super admin only)
# ---------------------------------------------------------------------------

@router.get("/tickets", response_model=PaginatedTickets)
async def list_support_tickets(
    status: SupportTicketStatus | None = Query(None),
    category: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.super_admin)),
):
    """List all support tickets across all tenants (super admin only)."""
    query = select(SupportTicket)

    if status:
        query = query.where(SupportTicket.status == status)
    if category:
        query = query.where(SupportTicket.category == category)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            SupportTicket.tenant_name.ilike(pattern)
            | SupportTicket.tenant_email.ilike(pattern)
            | SupportTicket.subject.ilike(pattern)
        )

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Paginate
    query = query.order_by(SupportTicket.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    tickets = result.scalars().all()

    return PaginatedTickets(
        items=tickets,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/tickets/{ticket_id}", response_model=SupportTicketResponse)
async def get_support_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.super_admin)),
):
    """Get a single support ticket with full details."""
    result = await db.execute(
        select(SupportTicket).where(SupportTicket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if ticket is None:
        raise HTTPException(status_code=404, detail="Support ticket not found")
    return ticket


@router.put("/tickets/{ticket_id}", response_model=SupportTicketResponse)
async def update_support_ticket(
    ticket_id: uuid.UUID,
    body: SupportTicketUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.super_admin)),
):
    """Update a support ticket status or admin notes."""
    result = await db.execute(
        select(SupportTicket).where(SupportTicket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if ticket is None:
        raise HTTPException(status_code=404, detail="Support ticket not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(ticket, field, value)

    await db.flush()
    await db.refresh(ticket)
    return ticket
