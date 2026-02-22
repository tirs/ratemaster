"""Data import service - CSV parsing and validation."""
import csv
import io
from datetime import datetime
from typing import Any

import pandas as pd

LOGICAL_FIELDS = [
    "stay_date",
    "rooms_available",
    "total_rooms",
    "rooms_sold",
    "adr",
    "total_rate",
    "revenue",
    "booking_date",
]

DEFAULT_MAPPING = {f: f for f in LOGICAL_FIELDS}


def detect_column_mapping(content: bytes | str) -> dict[str, str]:
    """Auto-detect column mapping from CSV headers. Returns logical_field -> csv_header."""
    try:
        df = pd.read_csv(
            io.BytesIO(content) if isinstance(content, bytes) else io.StringIO(content),
            nrows=0,
        )
    except Exception:
        return {}
    headers = list(df.columns)
    header_norm = {_normalize_header(h): h for h in headers}
    mapping: dict[str, str] = {}
    for logical in LOGICAL_FIELDS:
        if logical in df.columns:
            mapping[logical] = logical
        elif logical in header_norm:
            mapping[logical] = header_norm[logical]
        elif logical == "stay_date":
            for alias in ["date", "arrival", "check_in", "staydate"]:
                if alias in header_norm:
                    mapping["stay_date"] = header_norm[alias]
                    break
        elif logical == "adr":
            for alias in ["rate", "avg_rate", "average_daily_rate"]:
                if alias in header_norm:
                    mapping["adr"] = header_norm[alias]
                    break
        elif logical == "booking_date":
            for alias in ["booking_date", "book_date", "reservation_date"]:
                if alias in header_norm:
                    mapping["booking_date"] = header_norm[alias]
                    break
    return mapping


def _normalize_header(h: str) -> str:
    return str(h).strip().lower().replace(" ", "_").replace("-", "_")


def parse_csv(
    content: bytes | str,
    column_mapping: dict[str, str],
) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Parse CSV with column mapping. Returns (rows, errors).
    column_mapping: logical_field -> csv_header_name
    """
    errors: list[str] = []

    try:
        df = pd.read_csv(
            io.BytesIO(content) if isinstance(content, bytes) else io.StringIO(content)
        )
    except Exception as e:
        return [], [f"CSV parse error: {e}"]

    headers = list(df.columns)
    header_norm = {_normalize_header(h): h for h in headers}
    # Build mapping: logical -> actual column name (try exact, then normalized)
    mapping: dict[str, str] = {}
    for logical, csv_col in column_mapping.items():
        if not csv_col:
            continue
        if csv_col in df.columns:
            mapping[logical] = csv_col
        elif _normalize_header(csv_col) in header_norm:
            mapping[logical] = header_norm[_normalize_header(csv_col)]
        elif logical in header_norm:
            mapping[logical] = header_norm[logical]

    rows: list[dict[str, Any]] = []

    for idx, row in df.iterrows():
        raw = row.to_dict()
        mapped: dict[str, Any] = {}
        for logical, csv_col in mapping.items():
            if csv_col in raw and pd.notna(raw[csv_col]):
                mapped[logical] = raw[csv_col]
        if "stay_date" not in mapped:
            errors.append(f"Row {idx + 2}: missing stay_date")
            continue
        try:
            if isinstance(mapped["stay_date"], str):
                mapped["stay_date"] = pd.to_datetime(mapped["stay_date"]).date().isoformat()
            else:
                mapped["stay_date"] = str(mapped["stay_date"])
        except Exception:
            errors.append(f"Row {idx + 2}: invalid stay_date")
            continue
        for k in ["rooms_available", "total_rooms", "rooms_sold"]:
            if k in mapped:
                try:
                    mapped[k] = int(float(mapped[k]))
                except (ValueError, TypeError):
                    errors.append(f"Row {idx + 2}: invalid {k}")
        for k in ["adr", "total_rate", "revenue"]:
            if k in mapped:
                try:
                    mapped[k] = float(mapped[k])
                except (ValueError, TypeError):
                    errors.append(f"Row {idx + 2}: invalid {k}")
        if "booking_date" in mapped:
            try:
                if isinstance(mapped["booking_date"], str):
                    mapped["booking_date"] = pd.to_datetime(mapped["booking_date"]).date().isoformat()
                else:
                    mapped["booking_date"] = str(mapped["booking_date"])
            except Exception:
                mapped.pop("booking_date", None)
        mapped["raw_data"] = raw
        rows.append(mapped)

    return rows, errors


def compute_data_health(rows: list[dict], errors: list[str]) -> tuple[int, list[str]]:
    """
    Data health score 0-100 and recommended fixes.
    Returns (score, recommended_fixes).
    """
    fixes: list[str] = []
    if not rows:
        return 0, ["Upload data - no rows found"]

    score = 100
    if len(errors) > 0:
        penalty = min(30, len(errors) * 5)
        score -= penalty
        fixes.append(f"Fix {len(errors)} validation errors in uploaded data")
    if len(rows) < 7:
        score -= 20
        fixes.append("Add more rows - at least 7 days recommended for reliable analysis")

    dates = sorted({r.get("stay_date") for r in rows if r.get("stay_date")})
    if len(dates) >= 2:
        from datetime import datetime
        try:
            d0 = datetime.fromisoformat(dates[0]).date()
            d1 = datetime.fromisoformat(dates[-1]).date()
            expected = (d1 - d0).days + 1
            if len(dates) < expected * 0.9:
                score -= 10
                fixes.append("Fill missing dates - gaps detected in date range")
        except (ValueError, TypeError):
            pass

    adrs = [r.get("adr") for r in rows if r.get("adr") is not None]
    if len(adrs) > 2:
        import statistics
        mean_adr = statistics.mean(adrs)
        try:
            stdev = statistics.stdev(adrs)
            outliers = [a for a in adrs if abs(a - mean_adr) > 3 * stdev]
        except statistics.StatisticsError:
            outliers = []
        if outliers:
            score -= 5
            fixes.append("Review outliers - unusual ADR values detected")

    return max(0, min(100, score)), fixes
