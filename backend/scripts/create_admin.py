"""Create admin user. Run from backend dir: python -m scripts.create_admin"""
import asyncio
import os
import sys

# Add parent to path so app imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, init_db
from app.models.user import User
from app.services.auth import hash_password


async def create_admin(email: str, password: str) -> None:
    """Create or update admin user."""
    await init_db()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            user.hashed_password = hash_password(password)
            await session.commit()
            print(f"Updated password for existing user: {email}")
        else:
            user = User(
                email=email,
                hashed_password=hash_password(password),
            )
            session.add(user)
            await session.commit()
            print(f"Created admin user: {email}")
    print("Done.")


if __name__ == "__main__":
    email = os.environ.get("ADMIN_EMAIL", "tmuseta@flowtasks.io")
    password = os.environ.get("ADMIN_PASSWORD", "Simbarashe06@")
    asyncio.run(create_admin(email, password))
