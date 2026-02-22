"""Database connection and session."""
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.base import Base
from app.models.user import User
from app.models.organization import Organization, Property
from app.models.data_import import DataSnapshot, DataSnapshotRow
from app.models.engine import EngineRun, Recommendation
from app.models.feature_store import FeatureStore  # noqa: F401 - for create_all
from app.models.model_registry import ModelRegistry  # noqa: F401 - for create_all
from app.models.job import BackgroundJob  # noqa: F401 - for create_all
from app.models.property_event import PropertyEvent  # noqa: F401 - for create_all


engine = create_async_engine(
    settings.database_url,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create tables (use Alembic in production)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
