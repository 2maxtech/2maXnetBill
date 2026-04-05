import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class IPPool(BaseModel):
    __tablename__ = "ip_pools"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    router_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("routers.id"), nullable=False)
    range_start: Mapped[str] = mapped_column(String(15), nullable=False)
    range_end: Mapped[str] = mapped_column(String(15), nullable=False)
    subnet: Mapped[str] = mapped_column(String(18), nullable=False)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    router = relationship("Router", lazy="selectin")
