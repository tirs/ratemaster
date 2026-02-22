"""Organization membership and roles."""
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, generate_uuid


class OrgMember(Base):
    """Organization member with role: owner, full, gm, analyst."""

    __tablename__ = "org_members"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id")
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(32))  # owner, full, gm, analyst
