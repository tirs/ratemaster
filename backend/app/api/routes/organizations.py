"""Organization and property API routes."""
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, status, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.services.org_access import user_has_org_access
from app.database import get_db
from app.models.organization import Organization, Property
from app.models.org_member import OrgMember
from app.models.user import User
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    PropertyCreate,
    PropertyResponse,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationResponse)
async def create_organization(
    body: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrganizationResponse:
    """Create new organization (portfolio). Owner role assigned."""
    org = Organization(
        name=body.name,
        owner_id=current_user.id,
    )
    db.add(org)
    await db.flush()
    member = OrgMember(
        organization_id=org.id,
        user_id=current_user.id,
        role="owner",
    )
    db.add(member)
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        created_at=org.created_at,
        logo_url=None,
    )


@router.get("", response_model=list[OrganizationResponse])
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[OrganizationResponse]:
    """List organizations where user is owner or member."""
    from app.models.org_member import OrgMember

    member_org_ids = select(OrgMember.organization_id).where(
        OrgMember.user_id == current_user.id
    )
    result = await db.execute(
        select(Organization).where(
            (Organization.owner_id == current_user.id) |
            (Organization.id.in_(member_org_ids))
        )
    )
    orgs = result.scalars().all()
    return [
        OrganizationResponse(
            id=o.id,
            name=o.name,
            created_at=o.created_at,
            logo_url=f"/api/v1/organizations/{o.id}/logo" if o.logo_url else None,
        )
        for o in orgs
    ]


def _logo_path(org_id: str, ext: str = "png") -> Path:
    """Path to org logo file."""
    base = Path(__file__).resolve().parent.parent.parent.parent / settings.uploads_dir
    base.mkdir(parents=True, exist_ok=True)
    logos_dir = base / "org_logos"
    logos_dir.mkdir(exist_ok=True)
    return logos_dir / f"{org_id}.{ext}"


ALLOWED_LOGO_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_LOGO_SIZE = 2 * 1024 * 1024  # 2MB


@router.post("/{organization_id}/logo", response_model=OrganizationResponse)
async def upload_organization_logo(
    organization_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrganizationResponse:
    """Upload organization logo. Owner or full user only."""
    if not await user_has_org_access(db, current_user.id, organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    result = await db.execute(select(Organization).where(Organization.id == organization_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_LOGO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Logo must be PNG, JPG, or WebP",
        )
    content = await file.read()
    if len(content) > MAX_LOGO_SIZE:
        raise HTTPException(status_code=400, detail="Logo must be under 2MB")
    path = _logo_path(organization_id, ext.lstrip("."))
    path.write_bytes(content)
    org.logo_url = f"org_logos/{organization_id}{ext}"
    await db.flush()
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        created_at=org.created_at,
        logo_url=f"/api/v1/organizations/{org.id}/logo",
    )


@router.delete("/{organization_id}/logo", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization_logo(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove organization logo."""
    if not await user_has_org_access(db, current_user.id, organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    result = await db.execute(select(Organization).where(Organization.id == organization_id))
    org = result.scalar_one_or_none()
    if not org or not org.logo_url:
        return
    for ext in ["png", "jpg", "jpeg", "webp"]:
        path = _logo_path(organization_id, ext)
        if path.exists():
            path.unlink()
            break
    org.logo_url = None
    await db.flush()


@router.get("/{organization_id}/logo")
async def get_organization_logo(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Serve organization logo. Requires org access."""
    if not await user_has_org_access(db, current_user.id, organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    result = await db.execute(select(Organization).where(Organization.id == organization_id))
    org = result.scalar_one_or_none()
    if not org or not org.logo_url:
        raise HTTPException(status_code=404, detail="No logo")
    for ext in ["png", "jpg", "jpeg", "webp"]:
        path = _logo_path(organization_id, ext)
        if path.exists():
            return FileResponse(path, media_type=f"image/{ext}")
    raise HTTPException(status_code=404, detail="Logo file not found")


@router.post("/properties", response_model=PropertyResponse)
async def create_property(
    body: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PropertyResponse:
    """Create property under organization."""
    if not await user_has_org_access(db, current_user.id, body.organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    result = await db.execute(select(Organization).where(Organization.id == body.organization_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Organization not found")
    prop = Property(
        name=body.name,
        organization_id=body.organization_id,
    )
    db.add(prop)
    await db.flush()
    return PropertyResponse(
        id=prop.id,
        name=prop.name,
        organization_id=prop.organization_id,
        created_at=prop.created_at,
    )


@router.get("/properties", response_model=list[PropertyResponse])
async def list_properties(
    organization_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PropertyResponse]:
    """List properties (optionally filtered by organization)."""
    from app.services.org_access import get_org_ids_for_user

    org_ids = await get_org_ids_for_user(db, current_user.id)
    if not org_ids:
        return []
    query = select(Property).where(
        Property.organization_id.in_(org_ids)
    )
    if organization_id:
        query = query.where(Property.organization_id == organization_id)
    result = await db.execute(query)
    props = result.scalars().all()
    return [
        PropertyResponse(
            id=p.id,
            name=p.name,
            organization_id=p.organization_id,
            created_at=p.created_at,
        )
        for p in props
    ]
