# Sample Hotel Data for RateMaster Testing

Realistic hotel revenue CSVs for testing the RateMaster system. Generated with seasonality, day-of-week patterns, and occupancy variance.

## Files

| File | Rows | Use Case |
|------|------|----------|
| `hotel_current.csv` | 90 days | Current data upload (Engine A 0–30d, partial Engine B) |
| `hotel_current_extended.csv` | 180 days | Extended current for full Engine B (31–365d) coverage |
| `hotel_prior_year.csv` | 365 days | Prior year for YoY curves, Billing YoY, seasonality |

## Schema

- **stay_date** – YYYY-MM-DD
- **rooms_available** – Total sellable rooms (120)
- **total_rooms** – Same as rooms_available
- **rooms_sold** – Occupied rooms
- **adr** – Average Daily Rate ($)
- **total_rate** – Same as revenue
- **revenue** – rooms_sold × adr

## Regenerate

```bash
python scripts/generate_hotel_data.py
```

## Upload Order

1. **Prior year first** – Upload `hotel_prior_year.csv` as "Prior Year (YoY)"
2. **Current** – Upload `hotel_current.csv` or `hotel_current_extended.csv` as "Current Data"

Then run Engine A and Engine B from the Engines tab.
