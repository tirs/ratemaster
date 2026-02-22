"""Data import service tests."""
import io
from app.services.data_import import (
    parse_csv,
    compute_data_health,
    detect_column_mapping,
    _normalize_header,
)


def test_normalize_header():
    assert _normalize_header("Stay Date") == "stay_date"
    assert _normalize_header("ADR") == "adr"


def test_parse_csv_basic():
    content = b"stay_date,adr,revenue\n2024-01-01,100,5000\n2024-01-02,110,5500"
    mapping = {"stay_date": "stay_date", "adr": "adr", "revenue": "revenue"}
    rows, errors = parse_csv(content, mapping)
    assert len(rows) == 2
    assert rows[0]["stay_date"] == "2024-01-01"
    assert rows[0]["adr"] == 100.0
    assert len(errors) == 0


def test_compute_data_health():
    rows = [{"stay_date": "2024-01-01", "adr": 100} for _ in range(10)]
    score, fixes = compute_data_health(rows, [])
    assert 0 <= score <= 100
    assert isinstance(fixes, list)


def test_compute_data_health_empty():
    score, fixes = compute_data_health([], [])
    assert score == 0
    assert "no rows" in fixes[0].lower() or "upload" in fixes[0].lower()


def test_detect_column_mapping():
    content = b"Stay Date,ADR,Revenue,Rooms\n2024-01-01,100,5000,50\n2024-01-02,110,5500,52"
    mapping = detect_column_mapping(content)
    assert "stay_date" in mapping
    assert "adr" in mapping
    assert mapping["stay_date"] in ("Stay Date", "stay_date")


def test_parse_csv_with_booking_date():
    content = b"stay_date,booking_date,adr\n2024-01-15,2024-01-01,100\n2024-01-16,2024-01-02,110"
    mapping = {"stay_date": "stay_date", "booking_date": "booking_date", "adr": "adr"}
    rows, errors = parse_csv(content, mapping)
    assert len(rows) == 2
    assert rows[0].get("booking_date") == "2024-01-01"
