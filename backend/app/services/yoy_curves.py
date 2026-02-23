"""YoY trend curves - compute from prior_year data, apply to Engine B."""
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.data_import import DataSnapshot, DataSnapshotRow
from app.models.yoy_curves import YoYCurve

LEAD_TIME_BUCKETS = [(0, 7, "0_7"), (8, 14, "8_14"), (15, 30, "15_30"), (31, 60, "31_60"), (61, 365, "61_365")]


def _lead_time_bucket(days: int) -> str | None:
    """Map lead-time days to bucket."""
    for lo, hi, name in LEAD_TIME_BUCKETS:
        if lo <= days <= hi:
            return name
    return None


def compute_yoy_curves(db: Session, property_id: str) -> int:
    """
    Compute YoY curves from prior_year snapshot.
    curve_type: season_month (1-12), dow (0-6 Mon-Sun), lead_time (0_7, 8_14, etc).
    Lead-time curves only when booking_date exists in raw_data.
    Returns count of curves stored.
    """
    result = db.execute(
        select(DataSnapshot)
        .where(
            DataSnapshot.property_id == property_id,
            DataSnapshot.snapshot_type == "prior_year",
        )
        .order_by(DataSnapshot.created_at.desc())
        .limit(1)
    )
    snapshot = result.scalar_one_or_none()
    if not snapshot:
        return 0

    rows_result = db.execute(
        select(DataSnapshotRow).where(DataSnapshotRow.snapshot_id == snapshot.id)
    )
    rows = rows_result.scalars().all()

    by_month: dict[int, list[float]] = defaultdict(list)
    by_dow: dict[int, list[float]] = defaultdict(list)
    by_lead_time: dict[str, list[float]] = defaultdict(list)

    for r in rows:
        if not r.adr:
            continue
        try:
            dt = datetime.strptime(r.stay_date, "%Y-%m-%d")
            by_month[dt.month].append(float(r.adr))
            by_dow[dt.weekday()].append(float(r.adr))
            raw = r.raw_data or {}
            book_str = raw.get("booking_date")
            if book_str:
                try:
                    book_dt = datetime.strptime(book_str, "%Y-%m-%d")
                    lead_days = (dt - book_dt).days
                    if lead_days >= 0:
                        bucket = _lead_time_bucket(lead_days)
                        if bucket:
                            by_lead_time[bucket].append(float(r.adr))
                except (ValueError, TypeError):
                    pass
        except (ValueError, TypeError):
            continue

    all_adr = [float(r.adr) for r in rows if r.adr]
    base_avg = sum(all_adr) / len(all_adr) if all_adr else 100.0

    db.execute(delete(YoYCurve).where(YoYCurve.property_id == property_id))
    count = 0
    for month, vals in by_month.items():
        if vals:
            mult = sum(vals) / len(vals) / base_avg if base_avg else 1.0
            curve = YoYCurve(
                property_id=property_id,
                curve_type="season_month",
                bucket=str(month),
                multiplier=Decimal(str(round(mult, 4))),
            )
            db.add(curve)
            count += 1
    for dow, vals in by_dow.items():
        if vals:
            mult = sum(vals) / len(vals) / base_avg if base_avg else 1.0
            curve = YoYCurve(
                property_id=property_id,
                curve_type="dow",
                bucket=str(dow),
                multiplier=Decimal(str(round(mult, 4))),
            )
            db.add(curve)
            count += 1
    for bucket, vals in by_lead_time.items():
        if vals:
            mult = sum(vals) / len(vals) / base_avg if base_avg else 1.0
            curve = YoYCurve(
                property_id=property_id,
                curve_type="lead_time",
                bucket=bucket,
                multiplier=Decimal(str(round(mult, 4))),
            )
            db.add(curve)
            count += 1
    db.flush()
    return count


def get_yoy_multiplier(
    db: Session, property_id: str, stay_date: str, days_until_stay: int | None = None
) -> float:
    """
    Get combined YoY multiplier for stay_date (month + dow, optionally lead_time).
    When days_until_stay is provided, lead_time curve is included for Engine B.
    """
    try:
        dt = datetime.strptime(stay_date, "%Y-%m-%d")
    except (ValueError, TypeError):
        return 1.0

    components: list[float] = []

    result = db.execute(
        select(YoYCurve).where(
            YoYCurve.property_id == property_id,
            YoYCurve.curve_type == "season_month",
            YoYCurve.bucket == str(dt.month),
        )
    )
    c = result.scalar_one_or_none()
    components.append(float(c.multiplier) if c else 1.0)

    result = db.execute(
        select(YoYCurve).where(
            YoYCurve.property_id == property_id,
            YoYCurve.curve_type == "dow",
            YoYCurve.bucket == str(dt.weekday()),
        )
    )
    c = result.scalar_one_or_none()
    components.append(float(c.multiplier) if c else 1.0)

    if days_until_stay is not None:
        bucket = _lead_time_bucket(days_until_stay)
        if bucket:
            result = db.execute(
                select(YoYCurve).where(
                    YoYCurve.property_id == property_id,
                    YoYCurve.curve_type == "lead_time",
                    YoYCurve.bucket == bucket,
                )
            )
            c = result.scalar_one_or_none()
            if c:
                components.append(float(c.multiplier))

    if all(m == 1.0 for m in components):
        return 1.0
    return sum(components) / len(components)
