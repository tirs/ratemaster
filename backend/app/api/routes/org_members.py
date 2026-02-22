"""Organization members - invite GM, Analyst."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.organization import Organization
from app.models.org_member import OrgMember
from app.models.user import User
from app.services.org_access import user_has_org_access

router = APIRouter(prefix="/organizations", tags=["org_members"])


class InviteMemberRequest(BaseModel):
    organization_id: str
    email: EmailStr
    role: str  # full, gm, analyst


class UpdateRoleRequest(BaseModel):
    role: str  # full, gm, analyst


@router.post("/members")
async def invite_member(
    body: InviteMemberRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Invite user to org as GM or Analyst. Only owner can invite."""
    if body.role not in ("full", "gm", "analyst"):
        raise HTTPException(status_code=400, detail="Role must be full, gm, or analyst")

    result = await db.execute(
        select(Organization).where(
            Organization.id == body.organization_id,
            Organization.owner_id == current_user.id,
        )
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    user_result = await db.execute(select(User).where(User.email == body.email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = await db.execute(
        select(OrgMember).where(
            OrgMember.organization_id == body.organization_id,
            OrgMember.user_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already a member")

    member = OrgMember(
        organization_id=body.organization_id,
        user_id=user.id,
        role=body.role,
    )
    db.add(member)
    await db.flush()
    return {"invited": True, "role": body.role}


@router.get("/my-role")
async def get_my_role(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's role in organization."""
    from app.services.org_access import get_user_org_role

    role = await get_user_org_role(db, current_user.id, organization_id)
    if not role:
        raise HTTPException(status_code=404, detail="Not a member of this organization")
    return {"role": role}


@router.get("/members")
async def list_org_members(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List members of an organization. Owner or member can list."""
    from app.services.org_access import user_has_org_access

    if not await user_has_org_access(db, current_user.id, organization_id):
        raise HTTPException(status_code=404, detail="Organization not found")

    org_result = await db.execute(
        select(Organization, User.email)
        .join(User, Organization.owner_id == User.id)
        .where(Organization.id == organization_id)
    )
    org_row = org_result.first()
    members = []
    if org_row:
        org, owner_email = org_row
        members.append({
            "id": f"owner-{org.owner_id}",
            "user_id": org.owner_id,
            "email": owner_email,
            "role": "owner",
        })

    result = await db.execute(
        select(OrgMember, User.email)
        .join(User, OrgMember.user_id == User.id)
        .where(OrgMember.organization_id == organization_id)
    )
    for m, email in result.all():
        members.append({
            "id": m.id,
            "user_id": m.user_id,
            "email": email,
            "role": m.role,
        })
    return members


@router.delete("/members/{member_id}")
async def remove_member(
    member_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove member from org. Only owner can remove."""
    from app.services.org_access import get_user_org_role, role_can_manage_members

    result = await db.execute(
        select(OrgMember).where(
            OrgMember.id == member_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    org_id = member.organization_id
    role = await get_user_org_role(db, current_user.id, org_id)
    if not role_can_manage_members(role):
        raise HTTPException(
            status_code=403,
            detail="Only owner can remove members",
        )
    if member.role == "owner":
        raise HTTPException(
            status_code=400,
            detail="Cannot remove owner",
        )
    await db.delete(member)
    await db.flush()
    return {"removed": True}


@router.patch("/members/{member_id}/role")
async def update_member_role(
    member_id: str,
    body: UpdateRoleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change member role (gm/analyst). Only owner can change."""
    from app.services.org_access import get_user_org_role, role_can_manage_members

    role = body.role
    if role not in ("full", "gm", "analyst"):
        raise HTTPException(status_code=400, detail="Role must be full, gm, or analyst")
    result = await db.execute(
        select(OrgMember).where(OrgMember.id == member_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    role_check = await get_user_org_role(db, current_user.id, member.organization_id)
    if not role_can_manage_members(role_check):
        raise HTTPException(
            status_code=403,
            detail="Only owner can change member roles",
        )
    member.role = role
    await db.flush()
    return {"updated": True, "role": role}
