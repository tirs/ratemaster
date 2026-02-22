"""Model registry service tests."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.base import Base
from app.models.model_registry import ModelRegistry
from app.services.model_registry import get_active_model, register_model


@pytest.fixture
def db_session():
    """Sync session - uses same DB as app (postgres)."""
    url = settings.database_url.replace("+asyncpg", "")
    engine = create_engine(url, echo=False)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    try:
        yield session
        session.rollback()
    finally:
        session.close()


def test_register_model(db_session):
    """Register model creates and returns record."""
    reg = register_model(
        db_session,
        "test_model_reg",
        "v1.0.0",
        property_id=None,
        metadata_={"type": "heuristic"},
        set_active=True,
    )
    db_session.commit()
    assert reg.model_name == "test_model_reg"
    assert reg.version == "v1.0.0"
    assert reg.is_active is True


def test_get_active_model(db_session):
    """Get active returns most recently registered."""
    register_model(db_session, "m1_active", "v1", set_active=True)
    db_session.commit()
    reg = get_active_model(db_session, "m1_active")
    assert reg is not None
    assert reg.version == "v1"

    register_model(db_session, "m1_active", "v2", set_active=True)
    db_session.commit()
    reg2 = get_active_model(db_session, "m1_active")
    assert reg2.version == "v2"
