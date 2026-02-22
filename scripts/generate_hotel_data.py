#!/usr/bin/env python3
"""
Generate realistic hotel revenue CSV data for testing RateMaster.
Run from project root: python scripts/generate_hotel_data.py
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

ROOMS = 120
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "fixtures"
OUTPUT_DIR.mkdir(exist_ok=True)


def season_mult(d: date) -> float:
    """Seasonality: summer high, winter low."""
    month = d.month
    if month in (6, 7, 8):  # Summer
        return 1.15
    if month in (12, 1, 2):  # Winter
        return 0.88
    if month in (3, 4, 5, 9, 10, 11):  # Shoulder
        return 1.0
    return 1.0


def dow_mult(d: date) -> float:
    """Day of week: Fri-Sat premium."""
    w = d.weekday()  # 0=Mon, 6=Sun
    if w in (4, 5):  # Fri, Sat
        return 1.25
    if w == 6:  # Sun
        return 1.08
    return 1.0


def gen_row(d: date, base_adr: float = 135.0, base_occ: float = 0.72) -> dict:
    """Generate one day of realistic hotel data."""
    occ = base_occ * season_mult(d) * dow_mult(d) * (0.95 + random.uniform(0, 0.1))
    occ = max(0.55, min(0.92, occ))
    rooms_sold = min(ROOMS, int(ROOMS * occ))
    adr = base_adr * season_mult(d) * dow_mult(d) * (0.97 + random.uniform(0, 0.06))
    adr = round(adr, 2)
    revenue = round(rooms_sold * adr, 2)
    return {
        "stay_date": d.isoformat(),
        "rooms_available": ROOMS,
        "total_rooms": ROOMS,
        "rooms_sold": rooms_sold,
        "adr": adr,
        "total_rate": round(revenue, 2),
        "revenue": revenue,
    }


def write_csv(path: Path, rows: list[dict]):
    """Write CSV with headers."""
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {path} ({len(rows)} rows)")


def main():
    random.seed(42)

    # Current data: next 90 days from today
    today = date.today()
    current_rows = []
    for i in range(90):
        d = today + timedelta(days=i)
        current_rows.append(gen_row(d, base_adr=142.0, base_occ=0.74))
    write_csv(OUTPUT_DIR / "hotel_current.csv", current_rows)

    # Prior year: full 365 days
    prior_start = date(today.year - 1, 1, 1)
    prior_rows = []
    for i in range(365):
        d = prior_start + timedelta(days=i)
        prior_rows.append(gen_row(d, base_adr=138.0, base_occ=0.71))
    write_csv(OUTPUT_DIR / "hotel_prior_year.csv", prior_rows)

    # Extended current: 180 days for more engine coverage
    extended_rows = []
    for i in range(180):
        d = today + timedelta(days=i)
        extended_rows.append(gen_row(d, base_adr=142.0, base_occ=0.74))
    write_csv(OUTPUT_DIR / "hotel_current_extended.csv", extended_rows)

    print(f"\nSample data in {OUTPUT_DIR}")
    print("  hotel_current.csv       - 90 days (current)")
    print("  hotel_current_extended.csv - 180 days (Engine B range)")
    print("  hotel_prior_year.csv     - 365 days (prior year for YoY)")


if __name__ == "__main__":
    main()
