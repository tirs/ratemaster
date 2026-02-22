"""
Pluggable Market Data Adapter.
Swap sources without rewriting engines.
Options: third-party API, licensed feed, customer CSV, manual entry.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@dataclass
class MarketSnapshotData:
    """Market rate snapshot with metadata (adapter output)."""
    property_id: str
    compset_avg: float | None
    compset_min: float | None
    compset_max: float | None
    source: str
    timestamp: str
    stay_date: str | None = None


class MarketDataAdapter(ABC):
    """Abstract adapter - implement for each data source."""

    @abstractmethod
    def fetch(self, property_id: str, db: "Session") -> MarketSnapshotData | None:
        """Fetch latest market signals for property."""
        pass

    def fetch_and_store(self, property_id: str, db: "Session") -> bool:
        """
        Fetch from external source and store to DB. Returns True if new data
        was stored. For customer-provided data (manual/CSV), no external fetch;
        returns False. For third-party API, would fetch, store, return True.
        """
        return False


class ManualEntryAdapter(MarketDataAdapter):
    """Fetch from market_snapshots (manual entry or API-stored)."""

    def fetch(self, property_id: str, db: "Session") -> MarketSnapshotData | None:
        from sqlalchemy import select
        from app.models.market import MarketSnapshot

        result = db.execute(
            select(MarketSnapshot)
            .where(MarketSnapshot.property_id == property_id)
            .order_by(MarketSnapshot.snapshot_at.desc())
            .limit(1)
        )
        snap = result.scalar_one_or_none()
        if not snap:
            return None
        return MarketSnapshotData(
            property_id=property_id,
            compset_avg=float(snap.compset_avg) if snap.compset_avg else None,
            compset_min=float(snap.compset_min) if snap.compset_min else None,
            compset_max=float(snap.compset_max) if snap.compset_max else None,
            source=snap.source,
            timestamp=snap.snapshot_at.isoformat() if snap.snapshot_at else "",
            stay_date=snap.stay_date,
        )


class CustomerCsvAdapter(MarketDataAdapter):
    """Customer-provided rate shop CSV - parses and stores in market_snapshots."""

    def fetch(self, property_id: str, db: "Session") -> MarketSnapshotData | None:
        return ManualEntryAdapter().fetch(property_id, db)
