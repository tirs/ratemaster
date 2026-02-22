"""Organization access - owner or member with role-based permissions."""
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.org_member import OrgMember

# Role hierarchy: owner > full > gm > analyst
ROLES = ("owner", "full", "gm", "analyst")


async def get_user_org_role(
    db: AsyncSession, user_id: str, organization_id: str
) -> str | None:
    """
    Get user's role in org. Returns 'owner', 'full', 'gm', 'analyst', or None if no access.
    """
    result = await db.execute(
        select(Organization).where(
            Organization.id == organization_id,
            Organization.owner_id == user_id,
        )
    )
    if result.scalar_one_or_none():
        return "owner"
    result = await db.execute(
        select(OrgMember).where(
            OrgMember.organization_id == organization_id,
            OrgMember.user_id == user_id,
        )
    )
    m = result.scalar_one_or_none()
    return m.role if m and m.role in ("full", "gm", "analyst") else None


async def get_org_ids_for_user(db: AsyncSession, user_id: str) -> list[str]:
    """Org IDs where user is owner or member (for data queries)."""
    member_orgs = select(OrgMember.organization_id).where(
        OrgMember.user_id == user_id
    )
    result = await db.execute(
        select(Organization.id).where(
            or_(
                Organization.owner_id == user_id,
                Organization.id.in_(member_orgs),
            )
        )
    )
    return [r[0] for r in result.fetchall()]


def role_can_approve(role: str | None) -> bool:
    """Owner, Full user, and GM can mark recommendations as applied."""
    return role in ("owner", "full", "gm")


def role_can_edit_settings(role: str | None) -> bool:
    """Owner, Full user, and GM can edit property settings."""
    return role in ("owner", "full", "gm")


def role_can_invite(role: str | None) -> bool:
    """Only owner can invite members."""
    return role == "owner"


def role_can_manage_members(role: str | None) -> bool:
    """Only owner can remove or change member roles."""
    return role == "owner"


async def user_has_org_access(
    db: AsyncSession, user_id: str, organization_id: str
) -> bool:
    """Check if user is owner or member of org."""
    return await get_user_org_role(db, user_id, organization_id) is not None


async def user_has_property_access(
    db: AsyncSession, user_id: str, property_id: str
) -> bool:
    """Check if user has access to property via org."""
    from app.models.organization import Property

    result = await db.execute(
        select(Property)
        .join(Organization)
        .where(Property.id == property_id)
    )
    prop = result.scalar_one_or_none()
    if not prop:
        return False
    return await user_has_org_access(db, user_id, prop.organization_id)


async def user_can_approve_for_property(
    db: AsyncSession, user_id: str, property_id: str
) -> bool:
    """Check if user can approve recommendations for this property."""
    from app.models.organization import Property

    result = await db.execute(
        select(Property, Organization.owner_id)
        .join(Organization, Property.organization_id == Organization.id)
        .where(Property.id == property_id)
    )
    row = result.first()
    if not row:
        return False
    prop, owner_id = row
    if user_id == owner_id:
        return True
    m_result = await db.execute(
        select(OrgMember.role).where(
            OrgMember.organization_id == prop.organization_id,
            OrgMember.user_id == user_id,
        )
    )
    m = m_result.scalar_one_or_none()
    return role_can_approve(m if m else None)
