import enum
import uuid

from sqlalchemy import Enum, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class SupportTicketStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class SupportTicket(BaseModel):
    __tablename__ = "support_tickets"

    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SupportTicketStatus] = mapped_column(
        Enum(SupportTicketStatus), default=SupportTicketStatus.open, nullable=False
    )
    category: Mapped[str] = mapped_column(String(50), default="bug", nullable=False)  # bug, feature_request, question
    tenant_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tenant_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    chat_history: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string of conversation
    image_urls: Mapped[str | None] = mapped_column(Text, nullable=True)  # comma-separated URLs
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
